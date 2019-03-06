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
class NAME(TOKEN):
	pass
class STRING(TOKEN):
	pass
class FLOAT(TOKEN):
	pass
class INT(TOKEN):
	pass
class OP(TOKEN):
	pass
class EOF(TOKEN):
	pass

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
			while current!="\n" :
				advance()
		
		# endline
		if current == "\n":
			global line
			line+=1
			advance()
	
	# if its an empty string, eof
	if current =="":
		return EOF(None)

	# operators (there can be with a = behind)
	if current in "=!><-+/*":
		op = None
		advance()
		if current=="=":
			op = last+current
			advance()
		else:
			op = last
		return OP(op)
	
	# name
	if current.isalpha():
		n = ""
		while current.isalpha() or current.isdigit() :
			n += current
			advance()
		return NAME(n)

	# string
	if current == "\"":
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
	if current.isdigit():
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
	
	# should not get here unless it's the end of file
	print("Reached the end of parse function : type", type(current),"value", current, "length", len(current), "line", line)
	return


####################################
## the recursive code generator
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



def Program():
	global token
	# eventually those things will go into a parser class
	# if not for this, the parser thinks it's EOF
	advance()
	# if not for this, consume won't work at first
	token = next()
	return Statement()

def Statement():
	if consume(NAME, "hi", exact=True):
		inst = Equality()
		inst2 = Statement()
		inst.extend(inst2)
		return inst
	return []

def Equality():
	inst = Comparison()
	if 	consume(OP, "==", exact=True) or consume(OP, "!=", True):
		op = consumed
		inst2 = Comparison()
		inst.extend(inst2)
		inst.append(OP_EQ)
		# this will probably change very soon (why add pushes and pops when ops are free?)
		if op == "!=":
			inst.append(OP_NEG)
		return inst
	return inst

def Comparison():
	inst = Addition()
	if consume(OP, ">", exact=True) or consume(OP, ">=", True) or consume(OP, "<", exact=True) or consume(OP, "<=", True):
		op = consumed
		inst2 = Addition()
		inst.extend(inst2)
		if op == ">":
			inst.append(OP_GT)
			return inst
		if op == ">=":
			inst.append(OP_GTE)
			return inst
		if op == "<":
			inst.append(OP_LT)
			return inst
		if op == "<=":
			inst.append(OP_LTE)
			return inst
	return inst


def Addition():
	# might lead by a - or ! to negate number or bool
	negate  = False
	if consume(OP, "!-"):
		if type(token) is INT or type(token) is FLOAT:
			token.value *= -1
		else:
			negate = True
	
	inst = Multiply()
	while consume(OP,"+-"):
		op = consumed
		inst2 = Multiply()
		inst.extend(inst2)
		if op == "+":
			inst.append(OP_ADD)
		else:
			inst.append(OP_SUB)
	
	if negate:
		inst.append(OP_NEG)
	return inst

def Multiply():
	inst = Primary()
	while consume(OP, "*/"):
		op = consumed
		inst2 = Primary()
		inst.extend(inst2)
		if op == "*":
			inst.append(OP_MUL)
		if op == "/":
			inst.append(OP_DIV)
	return inst


def Primary():
	inst = []

	if consume(FLOAT):
		inst.append(OP_FLOAT)
		for b in struct.pack("f", consumed):
			inst.append(b)
		return inst
	
	if consume(INT):
		inst.append(OP_INT)
		val = consumed
		b = [val & 255, (val & 0xFF00) >> 8, (val & 0xFF0000)>>16, (val & 0xFF000000)>>24 ]
		inst.extend(b)
		return inst
	
	if consume(STRING):
		inst.append(OP_STRING)
		for c in consumed:
			inst.append(ord(c))
		inst.append(0)
		return inst
	
	
	global token
	if type(token) is not EOF: 
		print("Primary : illegal token", token, "line", line)
	token = next()
	return inst



####################################
## the filework
####################################

instructions = []
with open(args.input,'r') as file:
	instructions = Program()

print("instructions", instructions)
with open(args.output,'wb') as file:
	file.write(bytes(instructions))