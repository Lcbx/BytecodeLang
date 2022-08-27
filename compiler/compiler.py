from opcodes import *
from tokenizer import Tokenizer, NAME, STRING, FLOAT, INT, OP, AUX, TABS, EOF
import struct


####################################
## the machinery
####################################

token = None 	# token to consume
consumed = None # last token consumed

indentsExpected = 0 # expected identation level

# checks whether the current token is of chosen type and value without consuming it
# Type : type of token accepted
# value: exact value accepted
def Peek(Type, value=None):
	global token
	return type(token) is Type and (value == None or token.value == value)

# consumes the token currently being evaluated
def ConsumeToken():
	global token
	global consumed
	consumed = token.value
	token = next()

# consumes the current token if it is of the exact type and value
# Type : 	type of token accepted
# value: exact value accepted
def Consume(Type, value=None):
	match = Peek(Type, value)
	if match:
		ConsumeToken()
	return match

# consumes the current token if it is of type and value is in accepted array
# Type : 	type of token accepted
# accepted: list of possible char accepted
def ConsumeAny(Type, acceptedValues=None):
	global token
	match = (Type==None or Peek(Type)) and (acceptedValues==None or token.value in acceptedValues)
	if match:
		ConsumeToken()
	return match


# a function to show parse errors
errorCount = 0
def Error(*msg):
	global errorCount
	errorCount += 1
	print(f'Error {token.context} :', *msg)
 

# used for type analysis at compile time
# for now it only handles string, int, float, bool
# NOTE : compile time is significantly slowed by the need to allocate those nodes
@dataclass
class AST_Node: # AST means Abstract Syntax Tree
	type: 		object	# uses python types for now
	opcodes:	list 	# the generated code

ScopeCount = 0
Scopes = [{}]
def AddScope():
	global Scopes
	Scopes.append({})

def PopScope():
	global Scopes
	global ScopeCount
	ScopeCount -= len(Scopes[-1])
	Scopes.pop()

def GetScope():
	global Scopes
	return Scopes[-1]

# the variables
def Declare(type, name):
	global ScopeCount
	# TODO: fix: index of var is stored in opcode field
	GetScope()[name] = AST_Node(type, ScopeCount) 
	ScopeCount += 1

# packs a jump offset into 2 bytes
def JumpOffset(offset):
	return struct.pack('h', offset)

# the bytes for a jump
def Jump(offset):
	return (OP_JUMP, *JumpOffset(offset))

# the bytes for a conditional jump
def JumpIf(conditionOpcodes, offset, jumpIfTrue = True):
	ignoreOpNeg = False
	if conditionOpcodes[-1] == OP_NEG:
		jumpIfTrue = not jumpIfTrue
		ignoreOpNeg = True
	return ( *(conditionOpcodes[:-1] if ignoreOpNeg else conditionOpcodes), OP_JUMP_IF if jumpIfTrue else OP_JUMP_IF_FALSE, *JumpOffset( offset ) )

def JumpIfFalse(conditionOpcodes, offset):
	return JumpIf(conditionOpcodes, offset, False)

####################################
## the recursive code generator
####################################
next = None
def Program(file):
	global next
	global token
	
	next = Tokenizer(file)
	token = next()
	
	prog = Block()
	
	return prog

def Block():
	global indentsExpected
	inst = []
	
	# while there's more instructions to parse within the same indentation level
	while True:
		if indentsExpected!=0 and not Consume(TABS, indentsExpected):
			# indents expected is set to whatever the next indentation is
			indentsExpected = consumed if Consume(TABS) else 0
			return inst
		
		res = Statement()
		
		if not res:
			return inst
		
		inst.extend(res)

def Statement():
	inst =  Declaration()	 if Consume(NAME, 'def')   else \
			IfStatement()	 if Consume(NAME, 'if')    else \
			WhileStatement() if Consume(NAME, 'while') else \
			PrintStatement() if Consume(NAME, 'print') else \
			Assignment()	 if Peek(NAME)				else \
			Expression().opcodes # temporary
	
	return inst

def Declaration():
	if Consume(NAME):
		name = consumed
		if name in GetScope(): Error(name, 'already declared')
		if Consume(OP, '='):
			inst = Expression()
			Declare(inst.type, name)
			return inst.opcodes
		elif Consume(AUX, '('): Error('functions not implemented yet')
	else: Error('no name after def')

def Condition(statementName, expression, position = ''):
	if position: position += ' '
	if len(expression.opcodes)==0:	Error(f'{statementName} missing {position}condition to evaluate')
	if expression.type != bool:		Error(f'{statementName} {position}condition is not boolean ({expression.type})')
	return expression

def IfStatement():
	global indentsExpected
	
	conditions = []
	
	firstCond = Condition('if', Expression())
	indentsExpected += 1
	
	firstInst = Block() # Block returns instructions, not AST_Node
	if len(firstInst)==0:  Error('if missing instructions to jump over')
	conditions.append( (firstCond.opcodes, firstInst) )
	
	while Consume(NAME, 'elif'):
		otherCond = Condition('elif', Expression())
		indentsExpected += 1
		otherInst = Block() # Block returns instructions, not AST_Node
		if len(otherInst)==0:  Error('elif missing instructions to jump over')
		conditions.append( (otherCond.opcodes, otherInst) )
	
	
	elseInst = []
	if Consume(NAME, 'else'):
		indentsExpected += 1
		elseInst = Block() # Block returns instructions, not AST_Node
		if len(elseInst)==0:  Error('else missing instructions')
	
	# in this set of instructions :
	# 7 = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP, OP_JUMP, short (= 2 bytes)
	# 4 = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP
	
	total_offset = 0
	for cond in conditions:
		total_offset += (len(cond[0])+len(cond[1])+7)
	total_offset += (len(elseInst) if elseInst else -3) # no need for last jump
	
	inst = []
	for cond in conditions:
		total_offset -= (len(cond[0])+len(cond[1])+7)
		inst.extend( (*JumpIfFalse(cond[0], len(cond[1])+4), OP_POP, *cond[1] ) )
		if total_offset > 0:
			inst.extend( Jump(total_offset) )
	
	inst.extend( elseInst )
	
	return inst

def WhileStatement():
	global indentsExpected
	cond = Condition('while', Expression())
	indentsExpected += 1
	
	inst = Block() # Block returns instructions, not AST_Node
	if len(inst)==0:  Error('while missing instructions to loop over')
	
	# in this set of instructions :
	# 4 = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP
	# 5 = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP, OP_JUMP
	inst = [*JumpIfFalse(cond.opcodes, len(inst)+4), OP_POP, *inst, *Jump( - (len(inst)+len(cond.opcodes)+5) ) ]
	return inst

def PrintStatement():
	inst = Expression()
	if len(inst.opcodes)==0:  Error('print missing expression')
	inst = [ *inst.opcodes, OP_PRINT ]
	return inst

def Assignment():
	if Consume(NAME):
		name = consumed
		if name not in GetScope(): Error('unknown variable', name)
		elif Consume(OP, '='):
			inst = [ *Expression().opcodes, OP_STORE, GetScope()[name].opcodes ] # TODO: fix: index of var is stored in opcode field
			return inst
		elif Consume(AUX, '('): Error('functions not implemented yet')
		# NOTE: we allow lone expressions but not variables
		# 		this means that `-a` is allowed but `a` is not
		else: Error(f'lone variable {name}')

def Expression():
	# Note : over expresion, AST_Node is not used, Statements have no type, just instructions
	return OrExpression()

def OrExpression():
	firstCond = AndExpression()
	inst = firstCond
	
	if Peek(NAME, 'or'):
		Condition('or', firstCond, 'left')
		lastCond = firstCond
		otherConds = []
	
		OVERHEAD = 4 # 4 = OP_JUMP, short (= 2bytes), OP_POP
		total_offset = 1 - OVERHEAD
		while Consume(NAME, 'or'):
			otherCond = Condition('or', AndExpression(), 'right')
			otherConds.append(otherCond)
			
			total_offset+= (len(otherCond.opcodes)+ OVERHEAD)
			lastCond = otherCond
		
		for condition in otherConds:
			inst.opcodes = [ *JumpIf(inst.opcodes, total_offset), OP_POP, *condition.opcodes ]
			total_offset -= (len(condition.opcodes) + OVERHEAD)
	
	return inst

def AndExpression():
	firstCond = Equality()
	inst = firstCond
	
	if Peek(NAME, 'and'):
		Condition('and', firstCond, 'left')
		lastCond = firstCond
		otherConds = []
		
		OVERHEAD = 4 # 4 = OP_JUMP, short (= 2bytes), OP_POP
		total_offset = 1 - OVERHEAD
		while Consume(NAME, 'and'):
			otherCond = Condition('and', Equality(), 'right')
			otherConds.append(otherCond)
			
			total_offset+= (len(otherCond.opcodes)+ OVERHEAD)
			lastCond = otherCond
		
		for condition in otherConds:
			inst.opcodes = [*JumpIfFalse(inst.opcodes, total_offset), OP_POP, *condition.opcodes ]
			total_offset -= (len(condition.opcodes) + OVERHEAD)
	
	return inst

def Equality():
	inst = Comparison()
	if 	Consume(OP, '==') or Consume(OP, '!='):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Comparison()
		if len(inst2.opcodes)!=0:
			if 	 op == '==': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_EQ])
			elif op == '!=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_NEQ])
		else: Error('missing right operand after', op)
	return inst

def Comparison():
	inst = Addition()
	if Consume(OP, '>') or Consume(OP, '>=') or Consume(OP, '<') or Consume(OP, '<='):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Addition()
		if len(inst2.opcodes)!=0:
			if inst.type in (float, int) and inst2.type == inst.type:
				if 	 op == '>':	 inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_GT])
				elif op == '>=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_GTE])
				elif op == '<':	 inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_LT])
				elif op == '<=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_LTE])
			else: Error('operand types do not match', op)
		else: Error('missing right operand after', op)
	return inst


def Addition():
	# might lead by a - or ! to negate number or bool
	negate  = False
	boolean = False
	
	if Consume(OP, '-'):
		if consumed=='-' and ( type(token) is INT or type(token) is FLOAT ):
			token.value *= -1
		elif consumed=='-':
			negate = True
	elif Consume(OP, '!'):
		negate = True
		boolean= True
	
	inst = Multiply()
	if boolean and inst.type != bool:
		Error(f'! operation\'s rvalue is not boolean ({inst.type})', )
	
	while ConsumeAny(OP,'+-'):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Multiply()
		if  len(inst2.opcodes)!=0:
			if inst2.type == inst.type:
				if inst.type in (float, int, str) and op == '+': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_ADD])
				elif inst.type in (float, int   ) and op == '-': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_SUB])
			else: Error('operand types do not match', op)
		else: Error('missing right operand after', op)
		
	if negate: inst.opcodes = [*inst.opcodes, OP_NEG]
	
	return inst


def Multiply():
	inst = Primary()
	while ConsumeAny(OP, '*/'):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Primary()
		if len(inst2.opcodes)!=0:
			if inst.type in (float, int) and inst2.type == inst.type:
				if 	 op == '*' : inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_MUL])
				elif op == '/' : inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_DIV])
			else: Error('operand types do not match', op)
		else: Error('missing right operand after', op)
	return inst


def Primary():
	global token
	inst = AST_Node(None, [])
	
	if Consume(NAME):
		name = consumed
		if   name.upper() == "TRUE":
			inst = AST_Node( bool, [ OP_TRUE ])
		elif name.upper() == "FALSE":
			inst = AST_Node( bool, [ OP_FALSE ])
		elif name in GetScope():
			var = GetScope()[name]
			inst = AST_Node( var.type, [ OP_LOAD, var.opcodes ]) # TODO: fix: index of var is stored in opcode field
		else: Error('unknown name', name)

	elif Consume(FLOAT):
		inst = AST_Node(float, [ OP_FLOAT, *struct.pack('f', consumed) ])
	
	elif Consume(INT):
		val = consumed
		if 	 val>=-2**7 and val<2**7: 	inst = AST_Node(int, [ OP_INT1, *struct.pack('b', val) ])
		elif val>=-2**15 and val<2**15:	inst = AST_Node(int, [ OP_INT2, *struct.pack('h', val) ])
		elif val>=-2**31 and val<2**31:	inst = AST_Node(int, [ OP_INT4, *struct.pack('i', val) ])
		else: Error('value too high to be an int (use a float ?)')
	
	elif Consume(STRING):
		inst = AST_Node(str, [ OP_STRING, *map(ord,consumed), 0 ])
	
	elif Consume(AUX, '('):
		inst = Expression()
		if not Consume(AUX, ')'):
			Error('closing parenthesis ) missing')
	
	elif type(token) is not EOF: 
		Error(f'illegal token : \'{token}\'')
		token = next()
	return inst



####################################
## filework
####################################
if __name__ == '__main__':
	import argparse
	from extensions import DEFAULT_CODE_EXTENSION, DEFAULT_COMPILED_EXTENSION
	commandLineArgs = argparse.ArgumentParser(description='homemade compiler for project scripting language')
	commandLineArgs.add_argument('-i', '--input', nargs = '?',  help=f'path and name of code file', default = '../tests/test' + DEFAULT_CODE_EXTENSION )
	commandLineArgs.add_argument('-o', '--output', nargs = '?', help=f'path and name of compiled file (usual extension is {DEFAULT_COMPILED_EXTENSION})')
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs' )
	args = commandLineArgs.parse_args()
	
	if not args.output:
		args.output = args.input.replace(DEFAULT_CODE_EXTENSION, DEFAULT_COMPILED_EXTENSION)
	
	# trick for verbosity
	vprint = print if args.verbose else lambda a,*b:None
	
	instructions = []
	with open(args.input,'r') as file:
		instructions = Program(file)
		
	print(errorCount, 'errors')
	if errorCount == 0 :
		vprint( len(instructions), 'instructions', instructions)
		with open(args.output,'wb') as file:
			file.write(bytes(instructions))