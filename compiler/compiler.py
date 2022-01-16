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

# the variables
Variables = {}
def declare(name):
	Variables[name] = len(Variables)

# expected identation level
indents = 0

# packs a jump offset into 2 bytes
def jumpOffset(offset):
	return struct.pack('h', offset)

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
	global indents
	inst = []
	while True:
		if indents!=0 and not consumeExact(TABS, indents):
			return inst
		
		res = Statement()
		
		if not res:
			return inst
		
		inst.extend(res)

def Statement():
	inst =  Declaration() 	 if consumeExact(NAME, 'def')   else \
			WhileStatement() if consumeExact(NAME, 'while') else \
			Assignment()	 if consume(NAME)				else \
			Expression() # temporary
	
	return inst

def Declaration():
	if consume(NAME):
		name = consumed
		if name in Variables: Error(name, 'already declared')
		if consume(OP, '='):
			declare(name)
			inst = Expression()
			return inst
		elif consume(AUX, '('): Error('functions not implemented yet')
	else: Error('no name after def')
	
def Assignment():
	name = consumed
	if name not in Variables: Error('unknown variable', name)
	elif consume(OP, '='):
		inst = [ *Expression(), OP_STORE, Variables[name] ]
		return inst
	elif consume(AUX, '('): Error('functions not implemented yet')
	
	# NOTE: we allow lone expressions but not variables
	# 		this means that `-a` is allowed but `a` is not
	else: Error(f'lone variable {name}')

def WhileStatement():
	global indents
	cond = Expression()
	if len(cond)==0:  Error('while missing condition to evaluate')
	indents += 1
	inst = Block()
	if len(inst)==0:  Error('while missing instructions to loop over')
	# TODO : for all boolean jumps, replace OP_NEG by OP_JUMP_IF
	# maybe use a compiler function for this
	
	# in this set of instructions :
	# 4 = OP_JUMP_IF_FALSE, short, OP_POP
	# 5 = OP_JUMP_IF_FALSE, short, OP_POP, OP_JUMP
	
	inst = [*cond, OP_JUMP_IF_FALSE, *jumpOffset( len(inst)+4 ), OP_POP, *inst, OP_JUMP, *jumpOffset( - (len(inst)+len(cond)+5) ) ]
	return inst

def Expression():
	return OrExpression()

def OrExpression():
	conditions = []
	inst = AndExpression()
	OVERHEAD = 4 # 4 = OP_JUMP, <jump distance (short = 2bytes)>, OP_POP
	total_offset = 1 - OVERHEAD
	while consumeExact(NAME, 'or'):
		if len(inst)==0:  Error('or expression missing left operand')
		inst2 = AndExpression()
		if len(inst2)==0: Error('or expression missing right operand')
		conditions.append(inst2)
		total_offset+= (len(inst2)+ OVERHEAD)
	for cond in conditions:
		inst.extend([ OP_JUMP_IF, *jumpOffset(total_offset), OP_POP, *cond ])
	return inst

def AndExpression():
	conditions = []
	inst = Equality()
	OVERHEAD = 4 # 4 bytes = OP_JUMP, short (2 bytes), OP_POP
	total_offset = 1 - OVERHEAD
	while consumeExact(NAME, 'and'):
		if len(inst)==0:  Error('and expression missing left operand')
		inst2 = Equality()
		if len(inst2)==0: Error('and expression missing right operand')
		conditions.append(inst2)
		total_offset+= (len(inst2)+ OVERHEAD)
	for cond in conditions:
		inst.extend([ OP_JUMP_IF_FALSE, *jumpOffset(total_offset), OP_POP, *cond ])
		total_offset-= (len(cond)+ OVERHEAD)
	return inst

def Equality():
	inst = Comparison()
	if 	consumeExact(OP, '==') or consumeExact(OP, '!='):
		op = consumed
		if len(inst)==0: Error('missing left operand before', op)
		inst2 = Comparison()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == '==': inst.append(OP_EQ)
			elif op == '!=': inst.append(OP_NEQ)
		else: Error('missing right operand after', op)
	return inst

def Comparison():
	inst = Addition()
	if consumeExact(OP, '>') or consumeExact(OP, '>=') or consumeExact(OP, '<') or consumeExact(OP, '<='):
		op = consumed
		if len(inst)==0: Error('missing left operand before', op)
		inst2 = Addition()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == '>':	 inst.append(OP_GT)
			elif op == '>=': inst.append(OP_GTE)
			elif op == '<':	 inst.append(OP_LT)
			elif op == '<=': inst.append(OP_LTE)
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
		if len(inst)==0: Error('missing left operand before', op)
		inst2 = Multiply()
		inst.extend(inst2)
		if  len(inst2)!=0:
			if 	 op == '+':	inst.append(OP_ADD)
			elif op == '-': inst.append(OP_SUB)
		else: Error('missing right operand after', op)
	if negate: inst.append(OP_NEG)
	return inst


def Multiply():
	inst = Primary()
	while consume(OP, '*/'):
		op = consumed
		if len(inst)==0: Error('missing left operand before', op)
		inst2 = Primary()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == '*':	inst.append(OP_MUL)
			elif op == '/':	inst.append(OP_DIV)
		else: Error('missing right operand after', op)
	return inst


def Primary():
	global token
	inst = []

	if consume(NAME):
		name = consumed
		if consumed in Variables:
			inst = [ OP_LOAD, Variables[name] ]
		else: Error('unknown name', name)

	elif consume(FLOAT):
		inst = [ OP_FLOAT, *struct.pack('f', consumed) ]
	
	elif consume(INT):
		val = consumed
		if 	 val>=-2**7 and val<2**7: 	inst = [ OP_INT1, *struct.pack('b', val) ]
		elif val>=-2**15 and val<2**15:	inst = [ OP_INT2, *struct.pack('h', val) ]
		elif val>=-2**31 and val<2**31:	inst = [ OP_INT4, *struct.pack('i', val) ]
		else: Error('value too high to be an int (use a float ?)')
	
	elif consume(STRING):
		inst = [ OP_STRING, *map(ord,consumed), 0 ]
	
	elif consume(AUX, '('):
		inst = OrExpression()
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
		vprint('instructions', instructions)
		with open(args.output,'wb') as file:
			file.write(bytes(instructions))