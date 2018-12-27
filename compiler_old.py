from opcodes import *


opcodes = {}
for n, name in enumerate(operations):
	opcodes[name] = n

import argparse
parser = argparse.ArgumentParser(description='homemade compiler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "./test.txt", help='path and name of file' )
parser.add_argument("-o", '--output', nargs = '?', default = "./test.hex", help='path and name of file' )
args = parser.parse_args()


instructions = []

with open(args.input,'r') as file:
	for line in file:
		for word in line.split():
			ret = opcodes.get(word)
			if ret == None:
				ret = int(word)
			print( word + " " + str(ret) )
			instructions.append( ret )

#print(instructions)

with open(args.output,'wb') as file:
	file.write(bytes(instructions))
