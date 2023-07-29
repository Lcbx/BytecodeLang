from opcodes import *
import struct

opcodes = {}
for n, op in enumerate(operations):
	opcodes[n] = op

import argparse
commandLineArgs = argparse.ArgumentParser(description='homemade vm simulator for project scripting language')
commandLineArgs.add_argument('filepath', nargs = '?', default = '../tests/test.hex', help='path and name of file' )
commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs, and stop at each jump' )
commandLineArgs.add_argument('-b', '--bound', type=int, default = "-1", help='limits the number of operations executed' )
args = commandLineArgs.parse_args()

import sys

def verbosePrint(a, *args):
	print(a, args)
	sys.stdout.flush()

vprint = verbosePrint if args.verbose else lambda a,*b:None

with open(args.filepath,'rb') as file:

	stack = []
	
	scopes = []
	currentScope = 0
	
	content = file.read()
	index=0
	OPsExecuted = -1
	
	if len(content) == 0:
		print('file is empty !')
		
	while index<len(content):
		OPsExecuted +=1
		
		if args.bound > 0 and OPsExecuted > args.bound:
			print(f'... MAXIMUM OPERATION COUNT REACHED ({args.bound}) ...')
			sys.exit()
		
		opcode = content[index]
		opName = opcodes[opcode].name
		bytesConsumed = opcodes[opcode].bytesConsumed
		
		PADDING = ' ' * (5 - len(str(index)))
		print(f'{index}{PADDING}', end='\t')
		
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
		
		
		shouldWait = False
		
		def apply_jump(offset):
			global shouldWait
			global index
			index += offset
			if index > len(content) or index < 0: print('out of bounds jump !')
			if args.verbose: shouldWait = True
			
		try:
			if opcode == NO_OP: 
				pass
			elif opcode == OP_NONE: 
				stack.append(None)
			elif opcode == OP_TRUE: 
				stack.append(True)
			elif opcode == OP_FALSE:
				stack.append(False)
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
				var = stack[currentScope+value]
				stack.append(var)
				value = f'var{value} ({var})'
			elif opcode == OP_STORE:
				var = stack[currentScope+value]
				newVar = stack[-1] 
				stack[value] = newVar
				value = f'var{value} = {newVar} (was {var})'
			elif opcode == OP_POP:
				value = stack[-1]
				stack.pop()
			elif opcode == OP_JUMP:
				apply_jump(value)
				value = f'jumped {value}'
			elif opcode == OP_JUMP_IF:
				cond = stack[-1]
				if cond: apply_jump(value)
				value = ('' if cond else '!') + 'jump ' + str(value)
			elif opcode == OP_JUMP_IF_FALSE:
				cond = stack[-1]
				if not cond: apply_jump(value)
				value = ('!' if cond else '') + 'jump ' + str(value)
			elif opcode == OP_JUMP_IF_POP:
				cond = stack[-1]
				if cond: apply_jump(value)
				value = ('' if cond else '!') + 'jump ' + str(value)
				stack.pop()
			elif opcode == OP_JUMP_IF_FALSE_POP:
				cond = stack[-1]
				if not cond: apply_jump(value)
				value = ('!' if cond else '') + 'jump ' + str(value)
				stack.pop()
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
				if isinstance(value, bool):
					value = not value
				else:
					value = - value
				stack.pop()
				stack.append(value)
			elif opcode == OP_SCOPE_START:
				currentScope = len(stack)
				scopes.append( currentScope )
			elif opcode == OP_SCOPE_END:
				currentScope= scopes[-1]
				scopes.pop()
			elif opcode == OP_PRINT:
				value = f'print {stack[-1]}'
				stack.pop()
			elif opcode == OP_SHOW_STACK: 
				value = stack
			elif opcode == OP_END: 
				value = 'END'
			else:
				print(f'unknown opcode {opcode}:{opName}')
		except Exception as e:
			print(e)
		finally:
			print(opName, '=>', value, '--')
			if shouldWait: input('press Enter...')
