from opcodes import *
from tokenizer import Tokenizer, NAME, STRING, FLOAT, INT, OP, AUX, TABS, EOF
import struct


####################################
## the machinery
####################################

token = None 	# token to consume
consumed = None # last token consumed
# Type : 	type of token accepted
# accepted: list of possible char accepted
def consume(Type, accepted=None):
	global token
	global consumed
	if type(token) is Type:
		if accepted==None or token.value in accepted:
			#print(token)
			consumed = token.value
			token = next()
			return True
	return False
# Type : 	type of token accepted
# accepted: exact string accepted
def consumeExact(Type, accepted):
	global token
	global consumed
	if type(token) is Type:
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
class AST_Node:
	type: 		object	# uses python types for now
	opcodes:	list 	# the generated code


# the variables
Variables = {}
def declare(type, name):
	Variables[name] = AST_Node(type, len(Variables))

# expected identation level
indentsExpected = 0

# packs a jump offset into 2 bytes
def jumpOffset(offset):
	return struct.pack('h', offset)

# TODO: remove pop instructions and make JUMP_IF and JUMP_IF_FALSE automatically pop the stack (what of match statements though ?)

#def JumpIf(condition, offset):
#	jumpOp = OP_JUMP_IF
#	
#	# transform 'jump_if not condition' into jump_if_not condition'
#	if condition[-1] == OP_NEG:
#		jumpOp = OP_JUMP_IF_FALSE
#		condition = condition[:-1]
#	
#	return [ *condition, jumpOp, *jumpOffset(offset), OP_POP]

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
		if indentsExpected!=0 and not consumeExact(TABS, indentsExpected):
			return inst
		
		res = Statement()
		
		if not res:
			return inst
		
		inst.extend(res)

def Statement():
	inst =  Declaration() 	 if consumeExact(NAME, 'def')   else \
			WhileStatement() if consumeExact(NAME, 'while') else \
			Assignment()	 if consume(NAME)				else \
			Expression().opcodes # temporary
	
	return inst

def Declaration():
	if consume(NAME):
		name = consumed
		if name in Variables: Error(name, 'already declared')
		if consume(OP, '='):
			inst = Expression()
			declare(inst.type, name)
			return inst.opcodes
		elif consume(AUX, '('): Error('functions not implemented yet')
	else: Error('no name after def')
	
def Assignment():
	name = consumed
	if name not in Variables: Error('unknown variable', name)
	elif consume(OP, '='):
		inst = [ *Expression().opcodes, OP_STORE, Variables[name].opcodes ] # TODO: fix: index of var is stored in opcode field
		return inst
	elif consume(AUX, '('): Error('functions not implemented yet')
	
	# NOTE: we allow lone expressions but not variables
	# 		this means that `-a` is allowed but `a` is not
	else: Error(f'lone variable {name}')

def WhileStatement():
	global indentsExpected
	cond = Expression()
	if len(cond.opcodes)==0:  Error('while missing condition to evaluate')
	if cond.type != bool:  Error('while condition is not boolean', cond.type)
	indentsExpected += 1
	inst = Block() # Block returns instructions, not AST_Node
	if len(inst)==0:  Error('while missing instructions to loop over')
	# TODO : for all boolean jumps, replace OP_NEG by OP_JUMP_IF
	# maybe use a compiler function for this
	
	# in this set of instructions :
	# 4 = OP_JUMP_IF_FALSE, short, OP_POP
	# 5 = OP_JUMP_IF_FALSE, short, OP_POP, OP_JUMP
	
	inst = [*cond.opcodes, OP_JUMP_IF_FALSE, *jumpOffset( len(inst)+4 ), OP_POP, *inst, OP_JUMP, *jumpOffset( - (len(inst)+len(cond.opcodes)+5) ) ]
	return inst

def Expression():
	# Note : over expresion, AST_Node is not used, we just take instructions directly
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
		inst.opcodes.extend([ OP_JUMP_IF, *jumpOffset(total_offset), OP_POP, *condition.opcodes ])
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
		inst.opcodes.extend([ OP_JUMP_IF_FALSE, *jumpOffset(total_offset), OP_POP, *condition.opcodes ])
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
	elif consume(OP, '!'):
		negate = True
	
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
	if negate: inst.append(OP_NEG)
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
		if consumed in Variables:
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