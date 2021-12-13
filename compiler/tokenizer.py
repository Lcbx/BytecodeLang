from dataclasses import dataclass
from copy import copy

@dataclass
class TOKEN:
	value:	 object
	def __str__(self):
		return f'{type(self).__name__ }: {self.value}'
	def verbose(self):
		return f'{type(self).__name__ } at {self.context} : {self.value}'

class NAME(TOKEN): pass
class STRING(TOKEN): pass
class FLOAT(TOKEN): pass
class INT(TOKEN): pass
class OP(TOKEN): pass
class AUX(TOKEN): pass
class EOF(TOKEN): pass
	

@dataclass
class TokenizerContext:
	file: 	 object
	# current and column line in file
	line:    int = 0
	column:  int = 0
	# last and current char
	last: 	 str = ''
	current: str = ''
	
	def __str__(self):
		return f'line {self.line}, column {self.column}'
	
	def readCharacter(self):
		character = self.file.read(1)
		#print(character, end='', flush=True)
		return character

	# reads the next char
	def advance(self):
		self.last = self.current
		self.current = self.readCharacter()
		self.column += 1
		if self.current == '\n':
			self.line += 1
			self.column = 0
	
def Tokenizer(file):
	ctx = TokenizerContext(file, 0, 0, '', '')
	ctx.current = ctx.readCharacter()
	
	# generates 1 token at a time
	def next():
		advance = ctx.advance
		
		# non-relevant space
		while ctx.current in ' #\n' and ctx.current != '':
			# comments
			if ctx.current == '#':
				while ctx.current != '\n' and ctx.current != '':
					advance()
			advance()
		
		# if its an empty string, eof
		if ctx.current == '':
			return EOF(f'line {ctx.line}')
		
		
		# auxiliary
		if ctx.current in '\t[]{}()':
			aux = ctx.current
			advance()
			return AUX(aux)

		# operators (there can be with a = behind)
		elif ctx.current in '=!><-+/*':
			op = None
			advance()
			if ctx.current=='=':
				op = ctx.last+ctx.current
				advance()
			else:
				op = ctx.last
			return OP(op)
		
		# name
		elif ctx.current.isalpha():
			n = ''
			while ctx.current.isalpha() or ctx.current.isdigit():
				n += ctx.current
				advance()
			return NAME(n)

		# string
		elif ctx.current == '\'':
			s = ''
			advance()
			while (ctx.current != '\'' or ctx.last == '\\') and ctx.current != '':
				# escape character
				if ctx.current == '\\':
					advance()
					# newline
					if ctx.current == 'n':
						s += '\n'
					# string within string
					else:
						if ctx.current == '\'':
							s += '\''
						# right now we only support the above.
						# the escapes are otherwise left as is
						else:
							s += ('\\' + ctx.current)
				else:
					s += ctx.current
				advance()
			advance()
			return STRING(s)
		
		# number
		elif ctx.current.isdigit():
			n = ''
			while ctx.current.isdigit():
				n += ctx.current
				advance()
			# if there is a dot, it's a float
			if ctx.current == '.':
				n += ctx.current
				advance()
				while ctx.current.isdigit():
					n += ctx.current
					advance()
				return FLOAT(float(n))
			else:
				return INT(int(n))
				
		return AUX(ctx.current)
	
	# enrich token with context
	def enrichedToken():
		token = next()
		token.context = copy(ctx)
		return token
	
	return enrichedToken


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
		next = Tokenizer(file)
		token = None
		while type(token) is not EOF:
			token = next()
			print(token)
			results.append(str(token))
	
	vprint(results)
	with open(args.output,'w') as file:
		file.write('\n'.join(results))
		
		
