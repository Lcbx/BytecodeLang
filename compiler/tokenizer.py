from dataclasses import dataclass
from copy import copy

@dataclass
class TOKEN:
	value:	 object
	def __str__(self):
		return f'{type(self).__name__ }: {self.value}'
	def verbose(self):
		return f'{type(self).__name__ } at {self.context} : {self.value}'

class NAME  (TOKEN): pass
class STRING(TOKEN): pass
class FLOAT (TOKEN): pass
class INT   (TOKEN): pass
class OP    (TOKEN): pass
class AUX   (TOKEN): pass
class TABS  (TOKEN): pass
class EOF   (TOKEN): pass

# TODO : take into account use of tabs
# make a token to signal raising/lowering scope?

class Tokenizer:
	
	def __init__(self, file):
		self.file   = file
		# current and column line in file
		self.line   = 0
		self.column = 0
		# last and current char
		self.last   = ''
		self.current = self.readCharacter()
	
	def readCharacter(self):
		character = self.file.read(1)
		#print(character, end='', flush=True)
		return character
	
	def __str__(self):
		return f'line {self.line}, column {self.column}'

	# reads the next char
	def advance(self):
		self.column += 1
		if self.current == '\n':
			self.line += 1
			self.column = 0
		self.last = self.current
		self.current = self.readCharacter()
	
	# generates 1 token at a time
	def _next(self):
		advance = self.advance
		
		# ignore \n == eol
		if self.current == '\n':
			advance()
		
		#print("token line ", self.line, ",", self.column, ":", self.last, ",", self.current)
		# indentation level
		if self.column == 0:
			level = 0
			while self.current == '\t':
				level +=1
				advance()
			if level != 0:
				return TABS(level)
		
		# non-relevant space
		while self.current.isspace():
			advance()
		
		# comments
		if self.current == '#':
			while self.current != '\n':
				advance()
			advance()
		
		# if its an empty string, eof
		if self.current == '':
			return EOF(f'line {self.line}')
		
		
		# auxiliary
		if self.current in '\t[]{}()':
			aux = self.current
			advance()
			return AUX(aux)

		# operators (there can be with a = behind)
		elif self.current in '=!><-+/*':
			op = None
			advance()
			if self.current=='=':
				op = self.last+self.current
				advance()
			else:
				op = self.last
			return OP(op)
		
		# name
		elif self.current.isalpha():
			n = ''
			while self.current.isalpha() or self.current.isdigit():
				n += self.current
				advance()
			return NAME(n)

		# string
		elif self.current == '\'':
			s = ''
			advance()
			while (self.current != '\'' or self.last == '\\'):
				# escape character
				if self.current == '\\':
					advance()
					# newline
					if self.current == 'n':
						s += '\n'
					# string within string
					else:
						if self.current == '\'':
							s += '\''
						# right now we only support the above.
						# the escapes are otherwise left as is
						else:
							s += ('\\' + self.current)
				else:
					s += self.current
				advance()
			advance()
			return STRING(s)
		
		# number
		elif self.current.isdigit():
			n = ''
			while self.current.isdigit():
				n += self.current
				advance()
			# if there is a dot, it's a float
			if self.current == '.':
				n += self.current
				advance()
				while self.current.isdigit():
					n += self.current
					advance()
				return FLOAT(float(n))
			else:
				return INT(int(n))
				
		advance()
		return EOF(f'unhandled token : {self.current}')
	
	
	# enrich token with context
	def next(self):
		token = self._next()
		token.context = copy(self)
		return token
	
	# enrich token with context
	def __call__(self):
		return self.next()


####################################
## filework
####################################
if __name__ == '__main__':
	import argparse
	from extensions import DEFAULT_CODE_EXTENSION, DEFAULT_TOKENS_EXTENSION

	commandLineArgs = argparse.ArgumentParser(description='homemade compiler for project scripting language')
	commandLineArgs.add_argument('-i', '--input', nargs = '?',  help='path and name of file', default = '../tests/test' + DEFAULT_CODE_EXTENSION)
	commandLineArgs.add_argument('-o', '--output', nargs = '?', help=f'path and name of file (usual extension is {DEFAULT_TOKENS_EXTENSION})' )
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs')
	args = commandLineArgs.parse_args()
	
	if not args.output:
		args.output = args.input.replace(DEFAULT_CODE_EXTENSION, DEFAULT_TOKENS_EXTENSION)
		
	# trick for verbosity
	vprint = print if args.verbose else lambda a,*b:None

	results = []
	with open(args.input,'r') as file:
		tokenizer = Tokenizer(file)
		token = None
		while type(token) is not EOF:
			token = tokenizer()
			vprint(token)
			results.append(str(token))
	
	with open(args.output,'w') as file:
		file.write('\n'.join(results))
		
		
