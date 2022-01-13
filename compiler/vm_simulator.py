from opcodes import *
import struct

opcodes = {}
for n, op in enumerate(operations):
	opcodes[n] = op

import argparse
commandLineArgs = argparse.ArgumentParser(description='homemade vm simulator for project scripting language')
commandLineArgs.add_argument('-i', '--input', nargs = '?', default = '../tests/test.hex', help='path and name of file' )
commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs, and stop at each jump' )
args = commandLineArgs.parse_args()


vprint = print if args.verbose else lambda a,*b:None

with open(args.input,'rb') as file:
	#print('NOTE: OP_JUMP uses 3 bytes (OP and a short).\nSo a jump at indice 50 with an offset of 15 will get you to indice 68, NOT 65.')

	stack = []
	content = file.read()
	index=0
	
	while index<len(content):
		opcode = content[index]
		opName = opcodes[opcode].name
		bytesConsumed = opcodes[opcode].bytesConsumed
		print(index, ':', end='\t')
		value = ''
		index+=1
		if opcode == OP_STRING:
				c = content[index]
				while c!= 0 and  c != None:
					value+= chr(content[index])
					index+=1
					c = content[index]
				index+=1
		elif bytesConsumed !=0 and bytesConsumed!=None :
			fmt = None
			if op == OP_FLOAT: # put this before bytesConsumed == 4, since int4 also does
				value = readFloat()
			else:
				fmt = None
				if bytesConsumed != 0:
					if opcode == OP_FLOAT:
						fmt = 'f'
					elif bytesConsumed == 1:
						fmt = 'b'
					elif bytesConsumed == 2:
						fmt='h'
					elif bytesConsumed == 4:
						fmt = 'i'
					else:
						print('unknown number of bytes consumed :', bytesConsumed, ' for op ', opName )
					value = struct.unpack(fmt, content[index:index+bytesConsumed])[0]
					index += bytesConsumed
		
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
				stack.append(value)
			elif opcode == OP_INT2: 
				stack.append(value)
			elif opcode == OP_INT4: 
				stack.append(value)
			elif opcode == OP_FLOAT: 
				stack.append(value)
			elif opcode == OP_STRING:  
				stack.append(value)
			elif opcode == OP_LOAD:
				var = stack[value]
				stack.append(var)
				value = (value, var)
			elif opcode == OP_STORE:
				var = stack[value]
				newVar = stack[-1] 
				stack[value] = newVar
				value = (value,var,newVar)
			elif opcode == OP_POP:
				value = stack[-1]
				stack.pop()
			elif opcode == OP_JUMP:
				index+= value
				if args.verbose: input('press Enter...')
			elif opcode == OP_JUMP_IF:
				cond = stack[-1]
				if cond: index+= value 
				value = (value, cond)
				if args.verbose: input('press Enter...')
			elif opcode == OP_JUMP_IF_FALSE:
				cond = stack[-1]
				if not cond: index+= value 
				value = (value, cond)
				if args.verbose: input('press Enter...')
			elif opcode == OP_EQ: 
				value = stack[-2] == stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_NEQ: 
				value = stack[-2] != stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_LT: 
				value = stack[-2] < stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_LTE: 
				value = stack[-2] <= stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_GT: 
				value = stack[-2] > stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_GTE: 
				value = stack[-2] >= stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_ADD: 
				try:
					value = stack[-2] + stack[-1]
				except TypeError:
					value = str(stack[-2]) + str(stack[-1])
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_SUB: 
				value = stack[-2] - stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_MUL:
				value = stack[-2] * stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_DIV:
				value = stack[-2] / stack[-1]
				stack.pop()
				stack.pop()
				stack.append(value)
			elif opcode == OP_NEG:
				value = stack[-1]
				if cond is bool:
					value = not value
				else:
					value = - value
				stack.pop()
				stack.append(value)
			elif opcode == OP_PRINT:
				value = stack[-1]
				stack.pop()
				print(value)
			elif opcode == OP_SHOW_STACK: 
				value = stack
			elif opcode == OP_END: 
				value = 'END'
		except Exception as e:
			print(e)
		finally:
			print(opName, '=>', value, '--')
