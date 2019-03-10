from opcodes import *
import struct

opcodes = {}
for n, op in enumerate(operations):
	opcodes[n] = op

import argparse
parser = argparse.ArgumentParser(description='homemade disassembler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "../tests/test.hex", help='path and name of file' )
args = parser.parse_args()


with open(args.input,'rb') as file:
	content = file.read()
	i=0
	while i<len(content):
		opcode = content[i]
		print(i, ":", end="\t")
		val = ""
		if opcode == OP_STRING:
				i+=1
				c = content[i]
				while c!= 0 and  c != None:
					val+= chr(content[i])
					i+=1
					c = content[i]
				i+=1
		else:
			for j in range(opcodes[opcode].bytesConsumed):
				i+=1
				val += (str(content[i]) + " ")
			i+=1
		print(opcodes[opcode].name, val)