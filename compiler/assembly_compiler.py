from opcodes import *
from extensions import DEFAULT_COMPILED_EXTENSION, DEFAULT_ASSEMBLY_EXTENSION
import struct


opcodes = {}
for n, item in enumerate(operations):
	opcodes[item.name] = (n, item.bytesConsumed)

import argparse
commandLineArgs = argparse.ArgumentParser(description='homemade compiler for project scripting language')
commandLineArgs.add_argument('filepath', nargs = '?',  help='path and name of file', default = f'../tests/test{DEFAULT_ASSEMBLY_EXTENSION}' )
commandLineArgs.add_argument('-o', '--output', nargs = '?', help=f'path and name of file (usual extension is {DEFAULT_COMPILED_EXTENSION})')
args = commandLineArgs.parse_args()
if not args.output:
	args.output = args.filepath.replace(DEFAULT_ASSEMBLY_EXTENSION, DEFAULT_COMPILED_EXTENSION)


instructions = []

with open(args.filepath,'r') as file:
	content = file.read()
	
	if len(content) == 0:
		print('file is empty !')
		
	words = content.split()
	#print(words)
	
	i=0
	while i<len(words):
		word = words[i]
		opcodeAndbytesConsumed = opcodes.get(word)
		if opcodeAndbytesConsumed == None:
			print('unknown OP :', word)
		else:
			opcode, bytesConsumed = opcodeAndbytesConsumed
			instructions.append( opcode )
			if bytesConsumed != 0:
				i+=1
				val = None
				if bytesConsumed == 1:
					fmt = 'b'
				elif bytesConsumed == 2:
					fmt='h'
				elif bytesConsumed == 4:
					fmt = 'i'
				
				if 'FLOAT' in word:
					fmt = 'f'
					val = float(words[i])
				else:
					val = int(words[i])
				
				if val == None:
					print( f'unknown operation : {word} which consumes {bytesConsumed}' )
					continue
					
				#print(val)
				val = struct.pack(fmt, val)
				instructions.extend(val)
		i+=1


print(instructions)

if len(instructions)!=0:
	with open(args.output,'wb') as file:
		file.write(bytes(instructions))
