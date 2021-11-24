from opcodes import *
import struct


opcodes = {}
for n, item in enumerate(operations):
	opcodes[item.name] = (n, item.bytesConsumed)

import argparse
commandLineArgs = argparse.ArgumentParser(description='homemade compiler for project scripting language')
commandLineArgs.add_argument('-i', '--input', nargs = '?',  help='path and name of file', default = '../tests/test.ass' )
commandLineArgs.add_argument('-o', '--output', nargs = '?', help='path and name of file (usual extension is .hex)')
args = commandLineArgs.parse_args()
if not args.output:
	args.output = args.input.replace('.txt', '.hex')


instructions = []

with open(args.input,'r') as file:
	content = file.read()
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
