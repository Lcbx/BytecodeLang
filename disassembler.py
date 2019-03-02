from opcodes import *


opcodes = {}
for n, name in enumerate(operations):
	opcodes[n] = name

import argparse
parser = argparse.ArgumentParser(description='homemade disassembler for project scripting language')
parser.add_argument("-i", '--input', nargs = '?', default = "./test.hex", help='path and name of file' )
args = parser.parse_args()


with open(args.input,'r') as file:
	while True:
		opcode = file.read(1)
		if opcode == "":
			break
		opcode = ord(opcode)
		val = ""
		if opcode == OP_INT or opcode == OP_FLOAT:
			for i in range(4):
				c = file.read(1)
				if c == "":
					print("unexpected end of file while getting int or float value")
					exit()
				val += str(ord(c)) + " "
		else:
			if opcode == OP_STRING:
				c = file.read(1)
				while c!= chr(0) and  c != "" and c != None:
					val += str(ord(c)) + " "
					c = file.read(1)
			else:
				if opcode == OP_JUMP_IF:
					val = str(ord(file.read(1))) + " " + str(ord(file.read(1)))
		print(opcodes[opcode], val)