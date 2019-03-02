from opcodes import *
import argparse


parser = argparse.ArgumentParser(description='homemade compiler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "./test.txt", help='path and name of file' )
parser.add_argument("-o", '--output', nargs = '?', default = "./test.hex", help='path and name of file' )
args = parser.parse_args()

# token types enum
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

####################################
## parsing globals and utils
####################################

# current line in code
line = 0

# if we reached the end of file
EOF = False

# last and current char
last = ""
current = ""

# should stay instead of advance 
stay = False

# reads the next char
def advance():
	global stay
	if stay:
		stay = False
		return
	global last
	global current
	last = current
	current = file.read(1)
	global EOF
	if current == "":
		EOF = True
	# current = "" if end of file


####################################
## the the big tokenizer function
####################################

# generates 1 token at a time
def next():

	# non-relevant drivel
	while current == "" or current == " " or current == "#" or current == "\n":
		
		# empty string
		if current == "":
			# try advancing
			advance()
		
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
	
	# operators (there can be with a = behind)
	if current in "=!><-+/*" and current != "":
		advance()
		if current=="=":
			return OP(last+current)
		else:
			global stay
			stay = True
			return OP(last)
	
	# name
	if current.isalpha():
		n = ""
		while current.isalpha() :
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
def consume(Type):
	global token
	if token == None:
		token = next()
	if type(token) is Type:
		token = None
		return token.value
	return False


def Statement():
	inst_u = Unary()
	global EOF
	if EOF:
		return inst_u
	inst_s = Statement()
	inst_u.extend(inst_s)
	return inst_u
		
def Unary():
	prefix = consume(OP)
	inst_p = Primary()
	if prefix:
		if prefix == "!" or prefix == "-":
			inst_p.append(OP_NEG)
		else :
			print("unknown prefix operator", prefix, "line", line)
	return inst_p


import sys

def Primary():
	inst = []
	global token
	if token is None:
		token = next()
	
	print(token)
	sys.stdout.flush()

	if type(token) is FLOAT:
		#inst.append(OP_FLOAT)
		pass
	if type(token) is INT:
		inst.append(OP_INT)
		val = token.value
		b = [val & 255, (val & 0xFF00) >> 8, (val & 0xFF0000)>>16, val>>24 ]
		inst.extend(b)
	if type(token) is STRING:
		inst.append(OP_STRING)
		for c in token.value:
			inst.append(ord(c))
		inst.append(0)
	token = None
	print(inst)
	return inst







instructions = []
with open(args.input,'r') as file:
	instructions = Statement()

print("instructions", instructions)
with open(args.output,'wb') as file:
	file.write(bytes(instructions))