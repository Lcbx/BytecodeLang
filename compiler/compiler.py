from opcodes import *
from tokenizer import Tokenizer, NAME, STRING, FLOAT, INT, OP, AUX, TABS, EOF
import struct


####################################
## the machinery
####################################

token = None 	# token to consume
consumed = None # last token consumed

indentsExpected = 0 # expected identation level

# checks whether the current token is of chosen type without consuming it
# Type : 	type of token accepted
def peekType(Type):
	global token
	return type(token) is Type

# consumes the current token if it is of type and value is in accepted array
# Type : 	type of token accepted
# accepted: list of possible char accepted
def consume(Type, accepted=None):
	global token
	global consumed
	if peekType(Type):
		if accepted==None or token.value in accepted:
			#print(token)
			consumed = token.value
			token = next()
			return True
	return False
	
# consumes the current token if it is of the exact type and value
# Type : 	type of token accepted
# accepted: exact string accepted
def consumeExact(Type, accepted):
	global token
	global consumed
	if peekType(Type):
		if token.value == accepted:
			#print(token)
			consumed = token.value
			token = next()
			return True
	return False

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

Variables = {}
# the variables
def declare(variables, type, name):
	variables[name] = AST_Node(type, len(Variables))

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
	
	#variables = {}
	#methods = {}
	
	# while there's more instructions to parse within the same indentation level
	while True:
		if indentsExpected!=0 and not consumeExact(TABS, indentsExpected):
			# indents expected is set to whatever the next indentation is
			indentsExpected = consumed if consume(TABS) else 0
			return inst
		
		res = Statement()
		
		if not res:
			return inst
		
		inst.extend(res)

def Statement():
	inst =  Declaration()	 if consumeExact(NAME, 'def')   else \
			IfStatement()	 if consumeExact(NAME, 'if')    else \
			WhileStatement() if consumeExact(NAME, 'while') else \
			PrintStatement() if consumeExact(NAME, 'print') else \
			Assignment()	 if peekType(NAME)				else \
			Expression().opcodes # temporary
	
	return inst

def Declaration():
	if consume(NAME):
		name = consumed
		if name in Variables: Error(name, 'already declared')
		if consume(OP, '='):
			inst = Expression()
			declare(Variables, inst.type, name)
			return inst.opcodes
		elif consume(AUX, '('): Error('functions not implemented yet')
	else: Error('no name after def')

def Condition(statementName):
	cond = Expression()
	if len(cond.opcodes)==0:  Error(f'{statementName} missing condition to evaluate')
	if cond.type != bool:  Error(f'{statementName} condition is not boolean', cond.type)
	return cond

def IfStatement():
	global indentsExpected
	
	conditions = []
	
	firstCond = Condition('if')
	indentsExpected += 1
	firstInst = Block() # Block returns instructions, not AST_Node
	if len(firstInst)==0:  Error('if missing instructions to jump over')
	conditions.append( (firstCond.opcodes, firstInst) )
	
	while consumeExact(NAME, 'elif'):
		otherCond = Condition('elif')
		indentsExpected += 1
		otherInst = Block() # Block returns instructions, not AST_Node
		if len(otherInst)==0:  Error('elif missing instructions to jump over')
		conditions.append( (otherCond.opcodes, otherInst) )
	
	
	elseInst = []
	if consumeExact(NAME, 'else'):
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
	cond = Condition('while')
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
	if consume(NAME):
		name = consumed
		if name not in Variables: Error('unknown variable', name)
		elif consume(OP, '='):
			inst = [ *Expression().opcodes, OP_STORE, Variables[name].opcodes ] # TODO: fix: index of var is stored in opcode field
			return inst
		elif consume(AUX, '('): Error('functions not implemented yet')
	# NOTE: we allow lone expressions but not variables
	# 		this means that `-a` is allowed but `a` is not
	else: Error(f'lone variable {name}')

def Expression():
	# Note : over expresion, AST_Node is not used, Statements have no type, just instructions
	return OrExpression()

def OrExpression():
	firstCondition = AndExpression()
	lastCondition = firstCondition
	otherConditions = []
	
	OVERHEAD = 4 # 4 = OP_JUMP, <jump distance (short = 2bytes)>, OP_POP
	total_offset = 1 - OVERHEAD
	while consumeExact(NAME, 'or'):
		if len(lastCondition.opcodes)==0:  Error('or expression missing left operand')
		if lastCondition.type != bool: Error('or expression left operand is not boolean', lastCondition.type)
		
		otherCondition = AndExpression()
		if len(otherCondition.opcodes)==0: Error('or expression missing right operand')
		if otherCondition.type != bool: Error('or expression right operand is not boolean', otherCondition.type)
		otherConditions.append(otherCondition)
		
		total_offset+= (len(otherCondition.opcodes)+ OVERHEAD)
		lastCondition = otherCondition
	
	inst = firstCondition
	for condition in otherConditions:
		inst.opcodes = [ *JumpIf(inst.opcodes, total_offset), OP_POP, *condition.opcodes ]
		total_offset -= (len(condition.opcodes) + OVERHEAD)
	
	return inst

def AndExpression():
	firstCondition = Equality()
	lastCondition = firstCondition
	otherConditions = []
	
	OVERHEAD = 4 # 4 = OP_JUMP, <jump distance (short = 2bytes)>, OP_POP
	total_offset = 1 - OVERHEAD
	while consumeExact(NAME, 'and'):
		if len(lastCondition.opcodes)==0:  Error('and expression missing left operand')
		if lastCondition.type != bool: Error('and expression left operand is not boolean', lastCondition.type )
		
		otherCondition = Equality()
		if len(otherCondition.opcodes)==0: Error('and expression missing right operand')
		if otherCondition.type != bool: Error('and expression right operand is not boolean', otherCondition.type )
		otherConditions.append(otherCondition)
		
		total_offset+= (len(otherCondition.opcodes)+ OVERHEAD)
		lastCondition = otherCondition
	
	inst = firstCondition
	for condition in otherConditions:
		inst.opcodes = [*JumpIfFalse(inst.opcodes, total_offset), OP_POP, *condition.opcodes ]
		total_offset -= (len(condition.opcodes) + OVERHEAD)
	
	return inst

def Equality():
	inst = Comparison()
	if 	consumeExact(OP, '==') or consumeExact(OP, '!='):
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
	if consumeExact(OP, '>') or consumeExact(OP, '>=') or consumeExact(OP, '<') or consumeExact(OP, '<='):
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
	if consume(OP, '-'):
		if consumed=='-' and ( type(token) is INT or type(token) is FLOAT ):
			token.value *= -1
		elif consumed=='-':
			negate = True
	elif consume(OP, '!'):
		negate = True # TODO: check following expression is boolean
	
	inst = Multiply()
	while consume(OP,'+-'):
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
	while consume(OP, '*/'):
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
	
	if consume(NAME):
		name = consumed
		if   name.upper() == "TRUE":
			inst = AST_Node( bool, [ OP_TRUE ])
		elif name.upper() == "FALSE":
			inst = AST_Node( bool, [ OP_FALSE ])
		elif name in Variables:
			var = Variables[name]
			inst = AST_Node( var.type, [ OP_LOAD, var.opcodes ]) # TODO: fix: index of var is stored in opcode field
		else: Error('unknown name', name)

	elif consume(FLOAT):
		inst = AST_Node(float, [ OP_FLOAT, *struct.pack('f', consumed) ])
	
	elif consume(INT):
		val = consumed
		if 	 val>=-2**7 and val<2**7: 	inst = AST_Node(int, [ OP_INT1, *struct.pack('b', val) ])
		elif val>=-2**15 and val<2**15:	inst = AST_Node(int, [ OP_INT2, *struct.pack('h', val) ])
		elif val>=-2**31 and val<2**31:	inst = AST_Node(int, [ OP_INT4, *struct.pack('i', val) ])
		else: Error('value too high to be an int (use a float ?)')
	
	elif consume(STRING):
		inst = AST_Node(str, [ OP_STRING, *map(ord,consumed), 0 ])
	
	elif consume(AUX, '('):
		inst = Expression()
		if not consume(AUX, ')'):
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