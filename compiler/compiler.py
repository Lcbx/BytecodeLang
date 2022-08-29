from opcodes import *
from tokenizer import Tokenizer, NAME, STRING, FLOAT, INT, OP, AUX, TABS, EOF
import struct


####################################
## utility functions / structures
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
# NOTE : compile time is significantly slowed by the need to allocate these nodes
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

# simplify the bytes for a conditional jump if the boolean is inversed
# returns if confition was inversed
def simplifyJumpCond(conditionOpcodes):
	inversed = False
	if conditionOpcodes[-1] == OP_NEG:
		conditionOpcodes.pop()
		inversed =  True
	return inversed

def JumpIf(condOpcodes, offset):
	onFalse = simplifyJumpCond(condOpcodes)
	return _JumpIf(condOpcodes, offset, onFalse)
	
def JumpIfFalse(condOpcodes, offset):
	onTrue = simplifyJumpCond(condOpcodes)
	return _JumpIf(condOpcodes, offset, not onTrue)
	
def _JumpIf(condOpcodes, offset, inverse):
	return  ( *condOpcodes, OP_JUMP_IF_FALSE if inverse else OP_JUMP_IF, *JumpOffset( offset ) )


# jump opcode size constants
# TODO ? : remove OP_OP and merge it with OP_JUMP_IF/OP_JUMP_IF_FALSE
IF_OVERHEAD    = 4 # = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP
WHILE_OVERHEAD = 5 # = OP_JUMP_IF_FALSE, short (= 2 bytes), OP_POP, OP_JUMP
ELIF_OVERHEAD  = 3 # = ..., OP_JUMP, short (= 2 bytes)

####################################
## code generator
####################################
#
# it uses a recusive descent parser :
# we use the call stack as a way to create the parsing tree
# it's simple, relatively intuitive, and performant enough
# see https://www.geeksforgeeks.org/recursive-descent-parser/
#
# The Grammar used (might not be up to date) :
#
# Program
#  |->Block = [<Statement>]1+
#
# Statement
#	|-> Declaration    -> def <variable> = <Expression>
#	|-> IfStatement    -> if <boolean Expression> <Block> [elif <boolean Expression> <Block>]* [else <Block>]?
#	|-> WhileStatement -> while <boolean Expression> <Block>
#	|-> PrintStatement -> print <Expression>
#	|-> Assignment     -> <variable> = <Expression>
#	|-> Expression (temporary)
#
# Expression     -> <OrExpression>
# OrExpression   -> <AndExpression> [or <AndExpression>]*
# AndExpression  -> <Equality>      [and <Equality>]*
# Equality       -> <Comparison> [==|!=] <Comparison>
# Comparison     -> <Addition> [<|>|<=|>=] <Addition>
# Addition       -> <Multiplication> [[+|-] <Multiplication>]*
# Multiplication -> <Primary> [[*|/] <Primary>]*
# Primary        -> [true|false|<int>|<float>|<string>|<variable>|(<Expression>)]


def Program(file):
	global next
	global token
	
	next = Tokenizer(file)
	token = next()
	
	prog = Block()
	
	return prog

# a series of statements within the scope
# Note that Block returns instructions, not an AST_Node
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
	inst =  Declaration()	 if Peek(NAME, 'def')   else \
			IfStatement()	 if Peek(NAME, 'if')    else \
			WhileStatement() if Peek(NAME, 'while') else \
			PrintStatement() if Peek(NAME, 'print') else \
			Assignment()	 if Peek(NAME)				else \
			Expression().opcodes # temporary
	
	return inst

def Declaration():
	if Consume(NAME, 'def') and Consume(NAME):
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
	inst = []
	if Consume(NAME, 'if'):
	
		conditions = []
		firstCond = Condition('if', Expression())
		indentsExpected += 1
		
		firstInst = Block()
		if len(firstInst)==0:  Error('if missing instructions to jump over')
		
		def _addCondition(condition, instructions):
			conditions.append( (*JumpIfFalse(condition.opcodes, len(instructions)+IF_OVERHEAD), OP_POP, *instructions ) )
		
		_addCondition(firstCond, firstInst)
		
		while Consume(NAME, 'elif'):
			otherCond = Condition('elif', Expression())
			indentsExpected += 1
			otherInst = Block()
			if len(otherInst)==0:  Error('elif missing instructions to jump over')
			_addCondition(otherCond, otherInst)
		
		
		elseInst = []
		if Consume(NAME, 'else'):
			indentsExpected += 1
			elseInst = Block()
			if len(elseInst)==0:  Error('else missing instructions')
		
		total_offset = 0
		for cond in conditions:
			total_offset += (len(cond)+ELIF_OVERHEAD)
		total_offset += (len(elseInst) if elseInst else -ELIF_OVERHEAD) # no need for last jump
		
		for cond in conditions:
			total_offset -= (len(cond)+ELIF_OVERHEAD)
			inst.extend( cond )
			if total_offset > 0:
				inst.extend( Jump(total_offset) )
		
		inst.extend( elseInst )
	
	return inst

def WhileStatement():
	global indentsExpected
	inst = []
	if Consume(NAME, 'while'):
	
		cond = Condition('while', Expression())
		indentsExpected += 1
		
		inst = Block()
		if len(inst)==0:  Error('while missing instructions to loop over')
		
		inst = [*JumpIfFalse(cond.opcodes, len(inst)+IF_OVERHEAD), OP_POP, *inst, *Jump( - (len(inst)+len(cond.opcodes)+WHILE_OVERHEAD) ) ]
	return inst

def PrintStatement():
	inst = []
	if Consume(NAME, 'print'):
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
	# Note : over expression, AST_Node is not used, Statements have no type, just instructions
	return OrExpression()

# TODO!!! : ensure jump simplification does not mess with OrExpression/AndExpression
# see jump_optimisation_test_BUG.byte

def OrExpression():
	firstCond = AndExpression()
	inst = firstCond
	
	if Peek(NAME, 'or'):
		Condition('or', firstCond, 'left')
		otherConds = []
	
		total_offset = 1 - IF_OVERHEAD
		while Consume(NAME, 'or'):
			otherCondOps = Condition('or', AndExpression(), 'right').opcodes
			otherConds.append( (otherCondOps, simplifyJumpCond(otherCondOps)) )
			
			total_offset+= (len(otherCondOps)+ IF_OVERHEAD)
		
		for conditionOps, simplified in otherConds:
			inst.opcodes = [ *_JumpIf(inst.opcodes, total_offset, simplified), OP_POP, *conditionOps ]
			total_offset -= (len(conditionOps) + IF_OVERHEAD)
	
	return inst

def AndExpression():
	firstCond = Equality()
	inst = firstCond
	
	if Peek(NAME, 'and'):
		Condition('and', firstCond, 'left')
		otherConds = []
		
		total_offset = 1 - IF_OVERHEAD
		while Consume(NAME, 'and'):
			otherCondOps = Condition('and', Equality(), 'right').opcodes
			otherConds.append( (otherCondOps, simplifyJumpCond(otherCondOps)) )
			
			total_offset+= (len(otherCondOps)+ IF_OVERHEAD)
		
		for conditionOps, simplified in otherConds:
			inst.opcodes = [*_JumpIf(inst.opcodes, total_offset, not simplified), OP_POP, *conditionOps ]
			total_offset -= (len(conditionOps) + IF_OVERHEAD)
	
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
	
	inst = Multiplication()
	if boolean and inst.type != bool:
		Error(f'! operation\'s rvalue is not boolean ({inst.type})', )
	
	while ConsumeAny(OP,'+-'):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Multiplication()
		if  len(inst2.opcodes)!=0:
			if inst2.type == inst.type:
				if inst.type in (float, int, str) and op == '+': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_ADD])
				elif inst.type in (float, int   ) and op == '-': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_SUB])
			else: Error('operand types do not match', op)
		else: Error('missing right operand after', op)
		
	if negate: inst.opcodes = [*inst.opcodes, OP_NEG]
	
	return inst


def Multiplication():
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
	commandLineArgs.add_argument('filepath', nargs = '?',  help=f'path and name of code file', default = '../tests/test' + DEFAULT_CODE_EXTENSION )
	commandLineArgs.add_argument('-o', '--output', nargs = '?', help=f'path and name of compiled file (usual extension is {DEFAULT_COMPILED_EXTENSION})')
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs' )
	args = commandLineArgs.parse_args()
	
	if not args.output:
		args.output = args.filepath.replace(DEFAULT_CODE_EXTENSION, DEFAULT_COMPILED_EXTENSION)
	
	# trick for verbosity
	vprint = print if args.verbose else lambda a,*b:None
	
	instructions = []
	with open(args.filepath,'r') as file:
		instructions = Program(file)
		
	print(errorCount, 'errors')
	if errorCount == 0 :
		vprint( len(instructions), 'instructions', instructions)
		with open(args.output,'wb') as file:
			file.write(bytes(instructions))