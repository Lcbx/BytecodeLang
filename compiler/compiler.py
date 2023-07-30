from opcodes import *
from tokenizer import Tokenizer, NAME, STRING, FLOAT, INT, OP, AUX, TABS, EOF
import struct


####################################
## utility functions / structures
####################################

token = None 	# token waiting to be to consumed
consumed = None # last token consumed

# expected identation level
# set to 0 when parsing starts (see Program() and Block() functions)
indentsExpected = -1

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
	simple:		bool = True	# for boolean expressions, True by default, False when 'and' 'or' expressions are used
	
	# sets default value if not set
	def __post_init__(self):
		if self.simple is None:
			self.simple = True


# used for declaring/resolving variables
# TODO : to make function scope actually work,
#		we need to make variable adress be relative to local scope
#		since otherwise functions try to access the wrong global adress
# this means that we need addScope/popscope instructions

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
	#print('declared', name, type)

# the variables
def UnDeclare(name):
	global ScopeCount
	del GetScope()[name]
	ScopeCount -= 1
	#print('undeclared', name)


# used for declaring/resolving functions
functions = {}

@dataclass
class Function:
	parameters:	list 	# param names in order of declaration
	locals:		list	# local names in order of declaration
	opcodes:	list 	# the generated code


####################################
## jump utilities
####################################

# packs a jump offset into 2 bytes
def JumpOffset(offset):
	return struct.pack('h', offset)

# the bytes for a jump
def Jump(offset):
	return (OP_JUMP, *JumpOffset(offset))

# simplifies the bytes for a conditional jump if the boolean is inversed
# returns if condition was inversed
def simplifyJumpCond(conditionOpcodes):
	inversed = False
	while conditionOpcodes[-1] == OP_NEG:
	# Question :
	# Could we have a situation where a condition ends with the 25 (=OP_NEG) value (not the actual OP) ?
	# if so this could cause a major bug.
		conditionOpcodes.pop()
		inversed = not inversed
	return inversed


def _JumpIf(condOpcodes, offset, onFalse = False, simplify = False, NoPOP = False):
	
	if simplify:
		inversed = simplifyJumpCond(condOpcodes)
		if inversed:
			onFalse = not onFalse
	
	jumpOP = (OP_JUMP_IF_FALSE     if onFalse else OP_JUMP_IF) if NoPOP else \
			 (OP_JUMP_IF_FALSE_POP if onFalse else OP_JUMP_IF_POP)
	
	return  ( *condOpcodes, jumpOP, *JumpOffset( offset ) )
	
def JumpIfTrue(condOpcodes, offset):
	return _JumpIf(condOpcodes, offset)

def JumpIfFalse(condOpcodes, offset):
	return _JumpIf(condOpcodes, offset, onFalse=True)

def SimplifiedJumpIfFalse(condOpcodes, offset):
	return _JumpIf(condOpcodes, offset, onFalse=True, simplify=True)

def JumpIfTrue_NoPOP(condOpcodes, offset):
	return _JumpIf(condOpcodes, offset, NoPOP=True)
	
def JumpIfFalse_NoPOP(condOpcodes, offset):
	return _JumpIf(condOpcodes, offset, onFalse=True, NoPOP=True)

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
# -- NOTE : using recursion to exploit that "A or B or C" is equivalent to "A or (B or C)"
#
# Expression     -> <OrExpression>
# OrExpression   -> <AndExpression> [or  <OrExpression> ]?
# AndExpression  -> <Equality>      [and <AndExpression>]?
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
	indentsExpected += 1
	inst = []
	
	#print('Block start at ',token.context, token)
	
	# while there's more instructions to parse within the same indentation level
	while True:
		if indentsExpected!=0 and not Consume(TABS, indentsExpected):
			# indents expected is set to whatever the next indentation is
			indentsExpected = consumed if Consume(TABS) else 0
			#print('Block end at ',token.context, token)
			return inst
		
		res = Statement()
		
		# this is problematic but necessary
		# because lone expressions are accepted and can return empty if nothng is found
		if res == None:
			#print('Block end at ',token.context, token)
			return inst
		
		inst.extend(res)

def Statement():
	Consume(NAME)
	inst =  Declaration()	 if consumed == 'def'   else \
			IfStatement()	 if consumed == 'if'    else \
			WhileStatement() if consumed == 'while' else \
			PrintStatement() if consumed == 'print' else \
			Assignment()	 if Peek(OP, '=')       else \
			FunctionCall()	 if Peek(AUX, '(') else None
	
	# temporary
	if inst == None:
		inst = Expression().opcodes
		if not inst: inst = None
	
	return inst

def Declaration():
	if not Consume(NAME):
		Error('no name after def')
		return
	
	
	name = consumed
	if name in GetScope(): Error(f'variable {name} already declared')
	if name in functions:  Error(f'function {name} already declared')
	
	# variable
	if Consume(OP, '='):
		if token.value in functions:
			Consume(NAME)
			return FunctionCall(name)
		else:
			inst = Expression()
			Declare(inst.type, name)
			return inst.opcodes
	
	# function
	elif Consume(AUX, '('):
		AddScope()
		args = [] # ensure they are saved in declaration order
		while Consume(NAME):
			argName = consumed
			
			# TODO: find some way to ensure the call respects types
			# without explicit type (used here bc easier)
			Consume(NAME)
			type = int    if consumed == 'i' else \
				   float  if consumed == 'f' else \
				   string if consumed == 's' else \
				   bool   if consumed == 'b' else \
				   None
			Declare(type, argName) 
			
			args.append(argName)
			
			if Consume(AUX, ')'): break;
			if not Consume(AUX, ','): Error(name, 'function signature has unexpected tokens')
		if consumed != ')': Error(name, 'function signature not finished')
		
		inst = Block()
		locals = GetScope()
		PopScope()
		
		func = Function(args, locals, inst)
		functions[name] = func
		
		#print('function', func)
		#print('functions', functions)
		
		return []
	
	Error('Declaration : unreachable', name)

def FunctionCall( savedLocalName = None):
	name = consumed
	if not name in functions:
		Error(name, 'function has not been defined')
		return
	
	inst = []
	
	# parameters
	Consume(AUX,'(')
	func = functions[name]
	for local in func.parameters:
		inst.extend( Expression().opcodes )
		Consume(AUX,',')
	Consume(AUX,')')
	
	inst.extend( func.opcodes )
	
	if savedLocalName != None:
		for lName in func.locals.keys():
			Declare(func.locals[lName].type, f'{savedLocalName}.{lName}')
	
	return inst

def Condition(statementName, expression, position = ''):
	if position: position += ' '
	if len(expression.opcodes)==0:	Error(f'{statementName} missing {position}condition to evaluate')
	if expression.type != bool:		Error(f'{statementName} {position}condition is not boolean ({expression.type})')
	return expression

# jump opcode size constants
# parts between <> do not count toward constant
IF_OVERHEAD    = 3 # = <condition>, OP_JUMP_IF_FALSE, short (= 2 bytes), <content>
WHILE_OVERHEAD = 1 # = <similar to if statement>, OP_JUMP
ELIF_OVERHEAD  = 2 # = <if/elif statements>, OP_JUMP, short (= 2 bytes), <other elifs/else >
AND_OR_OVERHEAD= 0 # = <previous condition (with jump)>, <next condition/end>

def ConditionnalStatement(name):
	condition = Condition(name, Expression())
	
	instructions = Block()
	if len(instructions)==0:  Error(f'{name} missing instructions to jump over')
	
	jumpImplementation = SimplifiedJumpIfFalse if condition.simple else JumpIfFalse
	return [*jumpImplementation(condition.opcodes, len(instructions)+IF_OVERHEAD), *instructions]


def IfStatement():
	inst = []
	
	conditions = [ConditionnalStatement('if')]
	while Consume(NAME, 'elif'):
		conditions.append( ConditionnalStatement('elif') )
		
	instElse = []
	if Consume(NAME, 'else'):
		instElse = Block()
		if len(instElse)==0:   Error('else missing instructions')
		if Peek(NAME, 'elif'): Error('misplaced elif statement')
		if Peek(NAME, 'else'): Error('misplaced else statement')
	
	total_offset  = sum(map(lambda x:len(x)+ELIF_OVERHEAD, conditions)) + len(instElse)
	
	for cond in conditions:
		inst.extend( cond )
		total_offset -= (len(cond) + ELIF_OVERHEAD)
		if total_offset > 0:
			inst.extend( Jump(total_offset) )
	if instElse:
		inst.extend( instElse )
	
	return inst


def WhileStatement():
	inst = ConditionnalStatement('while')
	inst.extend( Jump( - (len(inst) + WHILE_OVERHEAD) ) )
	return inst

def PrintStatement():
	inst = Expression()
	if len(inst.opcodes)==0:  Error('print missing expression')
	inst = [ *inst.opcodes, OP_PRINT ]
	return inst

def Assignment():
	name = consumed
	if name not in GetScope():
		Error('unknown variable', name)
		return
	
	if Consume(OP, '='):
		inst = [ *Expression().opcodes, OP_STORE, GetScope()[name].opcodes ] # TODO: fix: index of var is stored in opcode field
		return inst
	
	Error('Assignment : unreachable', name)

def Expression():
	# Note : above this, AST_Node is not used
	# Statements have no type, just instructions
	inst = OrExpression()
	
	# cleanup any transitory variables from anonymous function call
	locals = list(GetScope().keys())
	for name in locals:
		if name[0] == '.': UnDeclare(name)
	
	return inst

def OrExpression():
	inst = AndExpression()
	
	if Consume(NAME, 'or'):
		Condition('or', inst, 'left')
		
		otherCondOPs = Condition('or', OrExpression(), 'right').opcodes
		inst.opcodes = [ *JumpIfTrue_NoPOP(inst.opcodes, len(otherCondOPs) + AND_OR_OVERHEAD), *otherCondOPs ]
		
		inst.simple = False
	
	return inst

def AndExpression():
	inst = Equality()
	
	if Consume(NAME, 'and'):
		Condition('and', inst, 'left')
		
		otherCondOPs = Condition('and', AndExpression(), 'right').opcodes
		inst.opcodes = [ *JumpIfFalse_NoPOP(inst.opcodes, len(otherCondOPs) + AND_OR_OVERHEAD), *otherCondOPs ]
		
		inst.simple = False
	
	return inst

def Equality():
	inst = Comparison()
	if 	Consume(OP, '==') or Consume(OP, '!='):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Comparison()
		if len(inst2.opcodes)==0: Error('missing right operand after', op)
		elif op == '==': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_EQ])
		elif op == '!=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_NEQ])
	return inst

def Comparison():
	inst = Addition()
	if Consume(OP, '>') or Consume(OP, '>=') or Consume(OP, '<') or Consume(OP, '<='):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Addition()
		if len(inst2.opcodes)==0: Error('missing right operand after', op)
		elif inst.type in (float, int) and inst2.type == inst.type:
			if 	 op == '>':	 inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_GT])
			elif op == '>=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_GTE])
			elif op == '<':	 inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_LT])
			elif op == '<=': inst = AST_Node(bool, [ *inst.opcodes,*inst2.opcodes, OP_LTE])
		else: Error(f'operand types ({inst2.type}, {inst.type}) do not match {op}')
	return inst


def Addition():
	# might lead by a - or ! to negate number or bool
	numberNegate  = False
	booleanNegate = False
	
	if Consume(OP, '-'):
		if type(token) is INT or type(token) is FLOAT:
			token.value *= -1
		else:
			numberNegate = True
	elif Consume(OP, '!'):
		booleanNegate = True
	
	inst = Multiplication()
	if booleanNegate and inst.type != bool:
		Error(f'! operation\'s rvalue is not boolean ({inst.type})')
	elif numberNegate and not inst.type in (float, int):
		Error(f'- operator\'s rvalue is not a number ({inst.type})')
	
	if numberNegate or booleanNegate :
		inst.opcodes = [*inst.opcodes, OP_NEG]
	
	while ConsumeAny(OP,'+-'):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Multiplication()
		if len(inst2.opcodes)==0: Error('missing right operand after', op)
		elif inst2.type == inst.type:
			if inst.type in (float, int, str) and op == '+': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_ADD])
			elif inst.type in (float, int   ) and op == '-': inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_SUB])
		else: Error(f'operand types ({inst2.type}, {inst.type}) do not match {op}')
	
	return inst


def Multiplication():
	inst = Primary()
	while ConsumeAny(OP, '*/'):
		op = consumed
		if len(inst.opcodes)==0: Error('missing left operand before', op)
		inst2 = Primary()
		if len(inst2.opcodes)==0: Error('missing right operand after', op)
		elif inst.type in (float, int) and inst2.type == inst.type:
			if 	 op == '*' : inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_MUL])
			elif op == '/' : inst = AST_Node(inst.type, [ *inst.opcodes,*inst2.opcodes, OP_DIV])
		else: Error(f'operand types ({inst2.type}, {inst.type}) do not match {op}')
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
		
		elif name in functions:
			# will declare locals as .<local>
			inst = FunctionCall("") 
			# .c => c in locals
			if Peek(NAME) and token.value[1:] in functions[name].locals:
				Consume(NAME)
				var = GetScope()[consumed]
				inst = AST_Node( var.type, inst + [ OP_LOAD, var.opcodes ])
			else: Error(f'invalid function call ({name})')
			
		else: Error('unknown name', name)
		return inst

	elif Consume(FLOAT):
		return AST_Node(float, [ OP_FLOAT, *struct.pack('f', consumed) ])
	
	elif Consume(INT):
		val = consumed
		if 	 val>=-2**7 and val<2**7: 	inst = AST_Node(int, [ OP_INT1, *struct.pack('b', val) ])
		elif val>=-2**15 and val<2**15:	inst = AST_Node(int, [ OP_INT2, *struct.pack('h', val) ])
		elif val>=-2**31 and val<2**31:	inst = AST_Node(int, [ OP_INT4, *struct.pack('i', val) ])
		else: Error('value too high to be an int (use a float ?)')
		return inst
	
	elif Consume(STRING):
		return AST_Node(str, [ OP_STRING, *map(ord,consumed), 0 ])
	
	elif Consume(AUX, '('):
		inst = Expression()
		if not Consume(AUX, ')'): Error('closing parenthesis ) missing')
		return inst
	
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