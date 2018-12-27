from opcodes import *
import argparse
import struct


parser = argparse.ArgumentParser(description='homemade compiler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "./test.txt", help='path and name of file' )
parser.add_argument("-o", '--output', nargs = '?', default = "./test.hex", help='path and name of file' )
args = parser.parse_args()


#########################
## CONSTANTS
#########################

words = {
	
	"None" : "NONE",
	"True" : "TRUE",
	"False" : "FALSE",
	
	"break" : "BREAK",
	"return" : "RETURN",
	
	"import" : "IMPORT",
	"is" : "IS",
	"this" : "THIS",
}

special_words = {

	"for" : "FOR",
	"while" : "WHILE",
	"if" : "IF",
	"else" : "ELSE",
	
}

lone_operators = {

	"(" : "LEFT_PAREN",
	")" : "RIGHT_PAREN",
	
	"[" : "LEFT_BRACKET",
	"]" : "RIGHT_BRACKET",
	
	"{" : "LEFT_BRACE",
	"}" : "RIGHT_BRACE",
	
	":" : "COLON",
	"." : "DOT",
	"," : "COMMA",
	"*" : "STAR",
	"/" : "SLASH",
	"%" : "PERCENT",
	"+" : "PLUS",
	"-" : "MINUS",
	"^" : "EXPONENT",
#	"&&" : "AND",
#	"||" : "OR",
#	"!" : "NOT",
	"?" : "QUESTION",
	
#	"=" : "EQ",
#	"==" : "EQEQ",
#	"!=" : "NOTEQ",
#	"<" : "LT",
#	">" : "GT",
#	"<=" : "LTE",
#	">=" "GTE",

}

other = [

	"NOTHING",
	"NAME",
	"STRING",
	"NUMERAL",
	"FLOAT",
	"CONTEXT",  # end of an if, for, while, class, ...
	
	"NOT",
	"EQ",
	"EQEQ",
	"NOTEQ",
	
	"AND",
	"OR",
	
	"LT",
	"GT",
	"LTE",
	"GTE",
	
	]
	
tokenValues = {}
tokenNames = []
slots = 0
# declares token codes and associates them with numbers (i just like this piece of code)
def declare(name, s = None):
	global slots
	exec("global %s\n%s = %d" % (name, name, slots))
	if s != None :
		tokenValues [s] = slots
		tokenNames.append(name)
	else:
		tokenNames.append(name)
	slots += 1


for s, name in words.items():
	declare(name, s)

for s, name in special_words.items():
	declare(name, s)

for s, name in lone_operators.items():
	declare(name, s)

# keep that last so opcodes match
for name in other:
	declare(name)
	
print (tokenValues)


#########################
## TOKENIZATION
#########################
	
tokens = []
expected_indents = 0

with open(args.input,'r') as file:
	
	for n, line in enumerate(file):
		
		# hack, gets rid of eof headache
		if line[-1]!="\n":
			line += "\n"
		
		print(line[:-1])
		
		index = 0
		indents = 0;
		
		def peek(n=1):
			return line[index-1+n]
			
		def next():
			c = peek()
			global index
			if index < len(line) :
				index +=1
			return c
			
		def addToken(type, val = None):
			global tokens
			tokens.append( (type, val, n, index) )
			
		
		while peek() == "\t":
			indents +=1
			next()
		if indents<expected_indents:
			addToken( CONTEXT )
			expected_indents = indents
		
		
		while index < len(line):
				
			mode = NOTHING
			s = ""
			
			def reset():
				mode = NOTHING
				s = ""
			
			# strings with escape
			if peek() == "\"":
				mode = STRING
				next()
				print("STRING ", peek(1), peek(2))
				while peek()!="\"":
					if peek(1)=="\\" and peek(2)=="\"":
						s+="\""
						next()
						next()
					else:
						s += next()
				addToken( STRING, s )
				reset()
			else:
				# words (either names of variables and classes or language-reserved)
				if peek().isalpha():
					print("NAME ", peek(1), peek(2))
					mode = NAME
					while peek().isalpha():
						s += next()
					if s in words or s in special_words:
						addToken( tokenValues[s] )
						if s in special_words:
							expected_indents +=1
					else :
						addToken( NAME, s )
					reset()
			
			
			# numbers
			if peek().isdigit():
				mode = NUMERAL
			while peek().isdigit():
				s += next()
				if peek() == ".":
					s+= next()
					mode = FLOAT					
					
			if mode == NUMERAL:
				addToken( NUMERAL, int(s) )
				reset()
			
			if mode == FLOAT:
				addToken( FLOAT, float(s) )
				reset()
			
			# binary operators
			if peek() in lone_operators:
				addToken(  tokenValues[next()] )
			else:			
				# probably a space, get on with your life
				next()
addToken( CONTEXT )


print(tokens)

#########################
## CODE GENERATION
#########################


# see http://www.craftinginterpreters.com/parsing-expressions.html

instructions = []

index = 0
indents = 0;

def peek(n=0):
	if index+n>=len(tokens):
		print("peeking further than possible!")
		return None
	return tokens[index+n]
def next():
	c = peek()
	global index
	if index < len(tokens) :
		index +=1
	return c
	
def consume(type):
	token = next()
	if token[0]!= type :
		t, val, line, index = token
		print("unexpected token : " + tokenNames[t] + (" of value " + (str(val)) if val!=None else "" ) + ", line", line, "char", index, "; expecting", tokenNames[type])
	return token
	
def Block():
	while peek()[0]!=CONTEXT:
		print("hi " + str(index)+"/"+str(len(tokens)))
		Statement()
	print("ENDED")

def Statement():
	Primary()
	return
	if peek()[0] == FOR:
		print("for")
		ForStmt()
		return
	if peek()[0] == WHILE:
		print("while")
		WhileStmt()
		return
	if peek(1)[0] == EQ:
		print("assign")
		AssignStmt()
		return
	print("declare")
	DeclarationStmt()
		
def WhileStmt():
	consume(WHILE)
	BoolExpresion()
	Block()

def ForStmt():
	consume(FOR)
	AssignStmt()
	consume(COMMA)
	BoolExpression()
	consume(COMMA)
	#Statement()
	Block()

def DeclarationStmt():
	print("next")
	next()
	
def AssignStmt():
	var = consume(NAME)
	consume(EQ)
	Expression()
	pass

def Expression():
	Primary()
	pass

def BoolExpression():
	pass
		
def Primary():
	token = next()
	if token[0] == FALSE:
		instructions.append(OP_FALSE)
	if token[0] == TRUE:
		instructions.append(OP_TRUE)
	if token[0] == NONE:
		instructions.append(OP_NONE)

	if token[0] == NUMERAL:                           
		instructions.append(OP_INT)
		val = token[1]
		b = [val>>24, (val & 0xFF0000)>>16, (val & 0xFF00) >> 8, val & 255 ]
		instructions.extend(b)
		print("INT : ", b)
	
	if token[0] == FLOAT:                           
		instructions.append(OP_FLOAT)
	
	if token[0] == STRING:                           
		instructions.append(OP_STRING)
		i = len(instructions)
		for c in token[1]:
			instructions.append(ord(c))
		instructions.append(0)
		print("string ", instructions[i:])
		
	if token[0] == LEFT_PAREN:                              
		expr = expression();                            
		consume(RIGHT_PAREN);                  
		
		
Block()
print("instructions", instructions)

with open(args.output,'wb') as file:
	file.write(bytes(instructions))
