from opcodes import *
import argparse
import struct


opcodes = {}
for n, item in enumerate(operations):
	opcodes[item.name] = (n, item.bytesConsumed)


parser = argparse.ArgumentParser(description='homemade compiler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "../tests/test.as.txt", help='path and name of file' )
parser.add_argument("-o", '--output', nargs = '?', default = "../tests/test.hex", help='path and name of file' )
args = parser.parse_args()


instructions = []

with open(args.input,'r') as file:
	content = file.read()
	words = content.split()
	#print(words)
	i=0
	while i<len(words):
		word = words[i]
		ret = opcodes.get(word)
		if ret == None:
			print("unknown OP :", ret)
		else:
			ret, bytesConsumed = (ret[0],ret[1])
			instructions.append( ret )
			if bytesConsumed != 0:
				i+=1
				if bytesConsumed == 1:
					fmt = "b"
				elif bytesConsumed == 2:
					fmt="h"
				elif bytesConsumed == 4:
					fmt = "i"
				else:
					print("unknown number of bytes consumed :", bytesConsumed, " for op ", opName )
				val = int(words[i])
				#print(val)
				val = struct.pack(fmt, val)
				instructions.extend(val)
		i+=1


print(instructions)

if len(instructions)!=0:
	with open(args.output,'wb') as file:
		file.write(bytes(instructions))
