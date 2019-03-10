from opcodes import *
import struct

opcodes = {}
for n, item in enumerate(operations):
	opcodes[n] = item

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
				c = chr(content[i])
				while c!= chr(0) and  c != "":
					i+=1
					c = chr(content[i])
		else:
			for j in range(opcodes[opcode][1]):
				i+=1
				val += (str(content[i]) + " ")
			i+=1
		print(opcodes[opcode][0], val)