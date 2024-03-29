from dataclasses import dataclass

@dataclass
class OP:
	name: 			str
	bytesConsumed:	object # to accept None

operations = [
	OP('NO_OP',    0),

	OP('OP_NONE',  0),
	OP('OP_TRUE',  0),
	OP('OP_FALSE', 0),
	OP('OP_INT1',  1), #-128@127
	OP('OP_INT2',  2), #-65536@65535
	OP('OP_INT4',  4), #MININT@MAXINT
	OP('OP_FLOAT', 4),
	OP('OP_STRING', None),
	
	OP('OP_LOAD',  1),
	OP('OP_STORE', 1),
	OP('OP_POP',   0),

	OP('OP_JUMP', 2),
	OP('OP_JUMP_IF', 2),
	OP('OP_JUMP_IF_FALSE', 2),
	OP('OP_JUMP_IF_POP', 2),
	OP('OP_JUMP_IF_FALSE_POP', 2),

	OP('OP_EQ',  0),
	OP('OP_NEQ', 0),
	OP('OP_LT',  0),
	OP('OP_LTE', 0),
	OP('OP_GT',  0),
	OP('OP_GTE', 0),

	OP('OP_ADD', 0),
	OP('OP_SUB', 0),
	OP('OP_MUL', 0),
	OP('OP_DIV', 0),
	OP('OP_NEG', 0),

	OP('OP_SCOPE_START', 0),
	OP('OP_SCOPE_END', 0),

	OP('OP_PRINT', 0),

	OP('OP_SHOW_STACK', 0),
	OP('OP_END', 0),
]

for n, op in enumerate(operations):
	# declares opcodes in python, usefull for compiler
	exec( f'{op.name} = {n}' )


####################################
## filework
####################################
if __name__ == '__main__':

	def readFile(filepath):
		with open(filepath,'r') as file:
			return file.read()
	
	def verifyAndReplace(filepath, expected):
		# verify if the contents are up to date
		content = readFile(filepath)
		# if they aren't, changes the file content
		if content != expected:
			with open(filepath,'w') as file:
				file.write(expected)
				print(f'{filepath} updated !')
			
	VM_OPCODES_FILE = '../vm/opcodes.h'
	VM_SWITCH_FILE  = '../vm/core.cpp'
	
	# used to enumerate and concatenate generated lines
	# generated by fnc based on operation number (n) and operation (op)
	def enumeratedOpsToStr(fnc):
		return ''.join( fnc(n, op) for n, op in enumerate(operations) )
	
	opcodes_cpp = readFile('./templates/opcodes.txt')
	fnc_opcodes = lambda n, op: f'const Byte { op.name } = { n };\n'
	opcodes_cpp = opcodes_cpp.replace('__OPCODES__', enumeratedOpsToStr(fnc_opcodes))
	verifyAndReplace(VM_OPCODES_FILE, opcodes_cpp)
	
	if False: # computed gotos. not supported by my current compiler
		switch_cpp = readFile('./templates/switch_goto.txt')
		fnc_labels = lambda n, op: f'&&{op.name}_LABEL, '
		fnc_dispatch = lambda n, op: f'\t\tcase {op.name}_LABEL: {op.name.lower()}(); {"DISPATCH()" if op != operations[OP_END] else ""}\n'
		switch_cpp = switch_cpp.replace('__LABELS__', enumeratedOpsToStr(fnc_labels))
		switch_cpp = switch_cpp.replace('__DISPATCH__', enumeratedOpsToStr(fnc_dispatch))
		verifyAndReplace(VM_SWITCH_FILE, switch_cpp)
	else: #simple switch case
		switch_cpp = readFile('./templates/switch_case.txt')
		fnc_dispatch = lambda n, op: f'\t\t\tcase {op.name}: {op.name.lower()}(); break;\n'
		switch_cpp = switch_cpp.replace('__DISPATCH__', enumeratedOpsToStr(fnc_dispatch))
		verifyAndReplace(VM_SWITCH_FILE, switch_cpp)
		

	
	