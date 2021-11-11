from opcodes import *
import struct

opcodes = {}
for n, op in enumerate(operations):
	opcodes[n] = op

import argparse
commandLineArgs = argparse.ArgumentParser(description='homemade vm simulator for project scripting language')
commandLineArgs.add_argument("-i", '--input', nargs = '?', default = "../tests/test.hex", help='path and name of file' )
args = commandLineArgs.parse_args()

with open(args.input,'rb') as file:
	#print("NOTE: OP_JUMP uses 3 bytes (OP and a short).\nSo a jump at indice 50 with an offset of 15 will get you to indice 68, NOT 65.")

	stack = []
	content = file.read()
	i=0
	
	while i<len(content):
		opcode = content[i]
		opName = opcodes[opcode].name
		bytesConsumed = opcodes[opcode].bytesConsumed
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
		elif bytesConsumed !=0 and bytesConsumed!=None :
			fmt = None
			if op == OP_FLOAT: # put this before bytesConsumed == 4, since int4 also does
				val = readFloat()
			else:
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
					val = struct.unpack(fmt, content[i:i+bytesConsumed])[0]
					i += bytesConsumed
		
		try:
			if opcode == NO_OP: 
				pass
			elif opcode == OP_NONE: 
				stack.append(None)
			elif opcode == OP_TRUE: 
				stack.append(True)
			elif opcode == OP_FALSE:
				stack.append(True)
			elif opcode == OP_INT1:
				stack.append(val)
			elif opcode == OP_INT2: 
				stack.append(val)
			elif opcode == OP_INT4: 
				stack.append(val)
			elif opcode == OP_FLOAT: 
				stack.append(val)
			elif opcode == OP_STRING:  
				stack.append(val)
			elif opcode == OP_LOAD:
				var = stack[val]
				stack.append(var)
				val = (val, var)
			elif opcode == OP_STORE:
				var = stack[val]
				stack[-1] = var
				stack.pop()
				val = (val,var)
			elif opcode == OP_POP:
				val = stack[-1]
				stack.pop()
			elif opcode == OP_JUMP:
				i+= val
			elif opcode == OP_JUMP_IF:
				cond = stack[-1]
				if cond: i+= val 
				val = (val, cond)
			elif opcode == OP_JUMP_IF_FALSE:
				cond = stack[-1]
				if not cond: i+= val 
				val = (val, cond)
			elif opcode == OP_EQ: 
				val = stack[-2] == stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_NEQ: 
				val = stack[-2] != stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_LT: 
				val = stack[-2] < stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_LTE: 
				val = stack[-2] <= stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_GT: 
				val = stack[-2] > stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_GTE: 
				val = stack[-2] >= stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_ADD: 
				try:
					val = stack[-2] + stack[-1]
				except TypeError:
					val = str(stack[-2]) + str(stack[-1])
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_SUB: 
				val = stack[-2] - stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_MUL:
				val = stack[-2] * stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_DIV:
				val = stack[-2] / stack[-1]
				stack.pop()
				stack.pop()
				stack.append(val)
			elif opcode == OP_NEG:
				val = stack[-1]
				if cond is bool:
					val = not val
				else:
					val = - val
				stack.pop()
				stack.append(val)
			elif opcode == OP_PRINT:
				val = stack[-1]
				stack.pop()
			elif opcode == OP_SHOW_STACK: 
				val = stack
			elif opcode == OP_END: 
				val = "END"
		except Exception as e:
			print(e)
		finally:
			print(opName, "=>", val, "--")
