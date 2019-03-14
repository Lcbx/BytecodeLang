from opcodes import *
import argparse
import struct

####################################
## script operands
####################################

parser = argparse.ArgumentParser(description='homemade compiler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "../tests/test.txt", help='path and name of file' )
parser.add_argument("-o", '--output', nargs = '?', default = "../tests/test.hex", help='path and name of file' )
args = parser.parse_args()

####################################
## token types enum
####################################
class TOKEN:
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return type(self).__name__ + ":" + str(self.value)

class NAME(TOKEN): pass
class STRING(TOKEN): pass
class FLOAT(TOKEN): pass
class INT(TOKEN): pass
class OP(TOKEN): pass
class AUX(TOKEN): pass
class EOF(TOKEN): pass

####################################
## parsing globals and utils
####################################

# current line in code
line = 0

# last and current char
last = ""
current = ""

# reads the next char
def advance():
	global last
	global current
	last = current
	current = file.read(1)
	#print(current, end="")
	# current == "" if end of file


####################################
## the big tokenizer function
####################################

# generates 1 token at a time
def next():

	# non-relevant drivel
	while current == " " or current == "#" or current == "\n":
			
		# puny spaces
		while current == " ":
			advance()

		# comments
		if current == "#":
			while current not in "\n" :
				advance()
		
		# endline
		if current == "\n":
			global line
			line+=1
			advance()
	
	# if its an empty string, eof
	if current =="":
		return EOF(None)
	
	# auxiliary
	if current in "\t[]{}()":
		aux = current
		advance()
		return AUX(aux)

	# operators (there can be with a = behind)
	elif current in "=!><-+/*":
		op = None
		advance()
		if current=="=":
			op = last+current
			advance()
		else:
			op = last
		return OP(op)
	
	# name
	elif current.isalpha():
		n = ""
		while current.isalpha() or current.isdigit() :
			n += current
			advance()
		return NAME(n)

	# string
	elif current == "\"":
		s = ""
		advance()
		while current != "\"" or last == "\\" :
			# escape character
			if current == "\\":
				advance()
				# newline
				if current == "n":
					s += "\n"
				# string within string
				else:
					if current == "\"":
						s += "\""
					# right now we only support the above.
					# the escapes are otherwise left as is
					else:
						s += ("\\" + current)
			else:
				s += current
			advance()
		advance()
		return STRING(s)
	
	# number
	elif current.isdigit():
		n = ""
		while current.isdigit():
			n += current
			advance()
		# if there is a dot, it's a float
		if current == ".":
			advance()
			while current.isdigit():
				n += current
				advance()
			return FLOAT(float(n))
		else:
			return INT(int(n))
	
	#print("Reached the end of parse function : type", type(current),"value", current, "length", len(current), "line", line)
	return AUX(current)


####################################
## code generation utilities
####################################

token = None
consumed = None
# Type : 	type of token accepted
# accepted: if exact==False : list of possible char accepted
#			if exact==True : exact string accepted
def consume(Type, accepted=None, exact=False):
	global token
	global consumed
	if type(token) is Type:
		if accepted==None or (not exact and token.value in accepted or
				 				  exact and token.value == accepted):
			#print(token)
			consumed = token.value
			token = next()
			return True
	return False

# a function to show parse errors
errorCount = 0
def Error(*msg):
	print("Error line", line+1, ":", *msg)
	global errorCount
	errorCount += 1

# the variables
Variables = {}
def declare(name):
	Variables[name] = len(Variables)


####################################
## the recursive code generator
####################################

def Program():
	global token
	# eventually those things will go into a parser class
	# if not for this, the parser thinks it's EOF
	advance()
	# if not for this, consume won't work at first
	token = next()
	prog = Statement()
	return prog

def Statement():
	inst = []
	if consume(NAME, "hi", exact=True):
		if consume(NAME, "def", exact=True):
			if consume(NAME):
				name = consumed
				if name in Variables: Error(name, "already declared")
				if consume(OP, "="):
					declare(name)
					inst = assign(name)
				elif consume(AUX, "("): Error("functions not implemented yet")
			else: Error("no name after def")
		elif consume(NAME):
			name = consumed
			if name not in Variables: Error(name, "not declared yet")
			elif consume(OP, "="):	inst = assign(name)
			elif consume(AUX, "("): Error("functions not implemented yet")
		else:
			inst = OrExpression()
		inst2 = Statement()
		inst.extend(inst2)
	return inst

def assign(name):
	inst = OrExpression()
	inst.append(OP_STORE)
	inst.append(Variables[name])
	return inst

def OrExpression():
	conditions = []
	inst = AndExpression()
	OVERHEAD = 4 # 4 = OP_JUMP, short, OP_POP
	total_offset = 1 - OVERHEAD
	while consume(NAME, "or", exact=True):
		if len(inst)==0: Error("or expression missing left operand")
		inst2 = AndExpression()
		if len(inst2)==0: Error("or expression missing right operand")
		conditions.append(inst2)
		total_offset+= (len(inst2)+ OVERHEAD)
	for cond in conditions:
		inst.extend([ OP_JUMP_IF, *struct.pack("h", total_offset), OP_POP, *cond ])
	return inst

def AndExpression():
	conditions = []
	inst = Equality()
	OVERHEAD = 4 # 4 = OP_JUMP, short, OP_POP
	total_offset = 1 - OVERHEAD
	while consume(NAME, "and", exact=True):
		if len(inst)==0: Error("and expression missing left operand")
		inst2 = Equality()
		if len(inst2)==0: Error("and expression missing right operand")
		conditions.append(inst2)
		total_offset+= (len(inst2)+ OVERHEAD)
	for cond in conditions:
		inst.extend([ OP_JUMP_IF_FALSE, *struct.pack("h", total_offset), OP_POP, *cond ])
		total_offset-= (len(cond)+ OVERHEAD)
	return inst

def Equality():
	inst = Comparison()
	if 	consume(OP, "==", exact=True) or consume(OP, "!=", True):
		op = consumed
		if len(inst)==0: Error("missing left operand before", op)
		inst2 = Comparison()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == "==": inst.append(OP_EQ)
			elif op == "!=": inst.append(OP_NEQ)
		else: Error("missing right operand after", op)
	return inst

def Comparison():
	inst = Addition()
	if consume(OP, ">=", exact=True) or consume(OP, ">=", True) or consume(OP, "<", exact=True) or consume(OP, "<=", True):
		op = consumed
		if len(inst)==0: Error("missing left operand before", op)
		inst2 = Addition()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == ">":	 inst.append(OP_GT)
			elif op == ">=": inst.append(OP_GTE)
			elif op == "<":	 inst.append(OP_LT)
			elif op == "<=": inst.append(OP_LTE)
		else: Error("missing right operand after", op)
	return inst


def Addition():
	# might lead by a - or ! to negate number or bool
	negate  = False
	if consume(OP, "!-"):
		if consumed=="-" and ( type(token) is INT or type(token) is FLOAT ):
			token.value *= -1
		else: negate = True
	
	inst = Multiply()
	while consume(OP,"+-"):
		op = consumed
		if len(inst)==0: Error("missing left operand before", op)
		inst2 = Multiply()
		inst.extend(inst2)
		if  len(inst2)!=0:
			if 	 op == "+":	inst.append(OP_ADD)
			elif op == "-": inst.append(OP_SUB)
		else: Error("missing right operand after", op)
	if negate: inst.append(OP_NEG)
	return inst


def Multiply():
	inst = Primary()
	while consume(OP, "*/"):
		op = consumed
		if len(inst)==0: Error("missing left operand before", op)
		inst2 = Primary()
		inst.extend(inst2)
		if len(inst2)!=0:
			if 	 op == "*":	inst.append(OP_MUL)
			elif op == "/":	inst.append(OP_DIV)
		else: Error("missing right operand after", op)
	return inst


def Primary():
	global token
	inst = []

	if consume(NAME):
		name = consumed
		if consumed in Variables:
			inst = [ OP_LOAD, Variables[name] ]
		else: Error("unknown name", name)

	elif consume(FLOAT):
		inst = [ OP_FLOAT, *struct.pack("f", consumed) ]
	
	elif consume(INT):
		val = consumed
		if 	 val>=-2**7 and val<2**7: 	inst = [ OP_INT1, *struct.pack("b", val) ]
		elif val>=-2**15 and val<2**15:	inst = [ OP_INT2, *struct.pack("h", val) ]
		elif val>=-2**31 and val<2**31:	inst = [ OP_INT4, *struct.pack("i", val) ]
		else: Error("value too high to be an int (use a float ?)")
	
	elif consume(STRING):
		inst = [ OP_STRING, *map(ord,consumed), 0 ]
	
	elif consume(AUX, "("):
		inst = OrExpression()
		if not consume(AUX, ")"): Error("closing parenthese ) missing")
	
	elif type(token) is not EOF: 
		Error("illegal token : \""+str(token.value)+"\"")
		token = next()
	return inst



####################################
## the filework
####################################

instructions = []
with open(args.input,'r') as file:
	instructions = Program()

print(errorCount, "errors")
print("instructions", instructions)

#if errorCount == 0 :
with open(args.output,'wb') as file:
	file.write(bytes(instructions))