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
class END_OF_FILE(TOKEN):
	pass

####################################
## parsing globals and utils
####################################

# current line in code
line = 0

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
	# returns "" if end of file


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
			# still nothing ? probably eof
			if current == "":
				return END_OF_FILE(None)

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
	
	# operators (can be with a = behind)
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
	#print("END", type(current), current,"-", len(current))
	return END_OF_FILE(None)


####################################
## the recursive code generator
####################################

def Statement():
	token = next()
	if type(token) is END_OF_FILE:		
		return
	print(type(token), token.value, "line", line)
	#equality()
	Statement()
	return token


instructions = []
with open(args.input,'r') as file:
	instructions = Statement()

print("instructions", instructions)
with open(args.output,'wb') as file:
	file.write(bytes(instructions))