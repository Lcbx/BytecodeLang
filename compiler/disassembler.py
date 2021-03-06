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
	#print("NOTE: OP_JUMP uses 3 bytes (OP and a short).\nSo a jump at indice 50 with an offset of 15 will get you to indice 68, NOT 65.")
	content = file.read()
	i=0
	while i<len(content):
		opcode = content[i]
		opName = opcodes[opcode].name
		print(i, ":", end="\t")
		val = ""
		i+=1
		if opcode == OP_STRING:
				c = content[i]
				while c!= 0 and  c != None:
					val+= chr(content[i])
					i+=1
					c = content[i]
				i+=1
		else:
			bytesConsumed = opcodes[opcode].bytesConsumed
			fmt = None
			if bytesConsumed != 0:
				if opcode == OP_FLOAT:
					fmt = "f"
				elif bytesConsumed == 1:
					fmt = "b"
				elif bytesConsumed == 2:
					fmt="h"
				elif bytesConsumed == 4:
					fmt = "i"
				else:
					print("unknown number of bytes consumed :", bytesConsumed, " for op ", opName )
				val += str(struct.unpack(fmt, content[i:i+bytesConsumed])[0])
				i += bytesConsumed
			
		print(opName, val)