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

	OP('OP_PRINT', 0),

	OP('OP_SHOW_STACK', 0),
	OP('OP_END', 0),
]

for n, op in enumerate(operations):
	# declares opcodes in python, usefull for compiler
	exec( f'{op.name} = {n}' )


def verifyAndReplace(filename, expected):
	# verify if the contents are up to date
	file = open(filename,'r')
	content = file.read()
	file.close()
	# if they aren't, changes the file content
	if content != expected:
		file = open(filename,'w')
		file.write(expected)
		file.close()
		print(f'{filename} updated !')


if __name__ == '__main__':

	VM_OPCODES_FILE = '../vm/opcodes.h'
	VM_SWITCH_FILE  = '../vm/core.cpp'

	# generates a header with all opcodes in cpp for the virtual machine
	opcodes_cpp = '''
#pragma once
#include "common.h"

// generated header, see opcodes.py
'''
	# generates the computed goto in cpp for the virtual machine
	# first part : header and declaration of labels
	switch_label_cpp = '''
#include "common.h"
#include "core.h"

// generated file, see opcodes.py
void Interpreter::execute_switch(){
	DEBUG(std::cout << "in execute\\n";)
	static const void* labels[] = {'''
	# the switch with all labels and calls to functions
	switch_dispatch_cpp = '''
	uchar opcode = 0;
	#define DISPATCH() opcode = code.next(); goto *labels[opcode];
	DISPATCH()
	while(false){
'''
	# used to enumerate and concatenate generated lines
	def enumeratedOpsToStr(fnc):
		return ''.join( fnc(n, op) for n, op in enumerate(operations) )
	
	def fnc_opcodes(n, op):
		return f'const uchar { op.name } = { n };\n'
	
	def fnc_labels(n, op):
		return f'&&{op.name}_LABEL, '
		
	def fnc_switch(n, op):
		dispatch = 'DISPATCH()' if op != operations[OP_END] else ''
		return f'\t\t{op.name}_LABEL: {op.name.lower()}(); {dispatch}\n'
		
	opcodes_cpp += enumeratedOpsToStr(fnc_opcodes)
	verifyAndReplace(VM_OPCODES_FILE, opcodes_cpp)
	
	switch_label_cpp     += enumeratedOpsToStr(fnc_labels) + '};'
	switch_dispatch_cpp  += enumeratedOpsToStr(fnc_switch) + '\t}\n}'
	switch_cpp = switch_label_cpp + switch_dispatch_cpp
	verifyAndReplace(VM_SWITCH_FILE, switch_cpp)

	
	