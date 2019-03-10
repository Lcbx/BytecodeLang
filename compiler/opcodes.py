# (op_name, bytes_taken)
operations = [

("NO_OP",    0),

("OP_NONE",  0),
("OP_TRUE",  0),
("OP_FALSE", 0),
("OP_INT1",  1), #-128@127
("OP_INT2",  2), #-65536@65535
("OP_INT4",  4), #MININT@MAXINT
("OP_FLOAT", 4),
("OP_STRING", None),

("OP_LOAD",  1),
("OP_STORE", 1),
("OP_POP",   0),

("OP_JUMP", 2),
("OP_JUMP_IF", 2),
("OP_JUMP_IF_FALSE", 2),

("OP_EQ",  0),
("OP_NEQ", 0),
("OP_LT",  0),
("OP_LTE", 0),
("OP_GT",  0),
("OP_GTE", 0),

("OP_ADD", 0),
("OP_SUB", 0),
("OP_MUL", 0),
("OP_DIV", 0),
("OP_NEG", 0),

("OP_PRINT", 0),

("OP_SHOW_STACK", 0),
("OP_END", 0),
]

for n, name in enumerate(map(lambda _:_[0], operations)):
	# declares opcodes in python
	exec( name + " = " + str(n) )


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
		print(filename + " updated !")


if __name__ == "__main__":

	VM_OPCODES_FILE = "../vm/opcodes.h"
	VM_SWITCH_FILE  = "../vm/core.cpp"

	# generates a header with all opcodes in cpp for the virtual machine
	opcodes_cpp = """
#pragma once
#include "common.h"

// generated header, see opcodes.py
"""
	# generates the computed goto in cpp for the virtual machine
	# first part : header and declaration of labels
	label_cpp = """
#include "common.h"
#include "core.h"

// generated file, see opcodes.py
void Interpreter::execute_switch(){
	DEBUG(std::cout << "in execute\\n";)
	static const void* labels[] = {"""
	# the switch with all labels and calls to functions
	switch_cpp = """
	uchar opcode = 0;
	#define DISPATCH() opcode = code.next(); goto *labels[opcode];
	DISPATCH()
	while(false){
"""
	for n, name in enumerate(map(lambda _:_[0], operations[:-1])):
		# opcode declaration
		opcodes_cpp += ("const uchar " + name + " = " + str(n) + ";\n")
		# label declaration
		label_cpp += ("&&"+ name + "_LABEL, ")
		# label and function call
		switch_cpp += ("\t\t" + name + "_LABEL: " + name.lower() + "(); DISPATCH()\n")
	

	# OP_END
	name = operations[-1][0]
	opcodes_cpp += ("const uchar " + name + " = " + str(len(operations)-1) + ";\n")
	label_cpp += ("&&"+ name + "_LABEL, ")
	switch_cpp += ("\t\t" + name + "_LABEL: " + name.lower() + "();\n")

	# end those puny braces
	label_cpp += "};"
	switch_cpp += "\t}\n}"

	verifyAndReplace(VM_OPCODES_FILE, opcodes_cpp)
	verifyAndReplace(VM_SWITCH_FILE, label_cpp+switch_cpp)

	
	