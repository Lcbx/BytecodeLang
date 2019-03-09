operations = [

"NO_OP",

"OP_NONE",
"OP_TRUE",
"OP_FALSE",
"OP_INT1", #-128@127
"OP_INT2", #-65536@65535
"OP_INT4", #MININT@MAXINT
"OP_FLOAT",
"OP_STRING",

"OP_LOAD",
"OP_STORE",
"OP_POP",
#"OP_COPY",

"OP_JUMP",
"OP_JUMP_IF",
"OP_JUMP_IF_FALSE",

"OP_EQ",
"OP_NEQ",
"OP_LT",
"OP_LTE",
"OP_GT",
"OP_GTE",

"OP_ADD",
"OP_SUB",
"OP_MUL",
"OP_DIV" ,
"OP_NEG",

"OP_PRINT",


"OP_PRINT_CHAR",
"OP_SHOW_STACK",

"OP_END",
]

for n, name in enumerate(operations):
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
	for n, name in enumerate(operations[:-1]):
		# opcode declaration
		opcodes_cpp += ("const uchar " + name + " = " + str(n) + ";\n")
		# label declaration
		label_cpp += ("&&"+ name + "_LABEL, ")
		# label and function call
		switch_cpp += ("\t\t" + name + "_LABEL: " + name.lower() + "(); DISPATCH()\n")
	

	# OP_END
	name = operations[-1]
	opcodes_cpp += ("const uchar " + name + " = " + str(len(operations)-1) + ";\n")
	label_cpp += ("&&"+ name + "_LABEL, ")
	switch_cpp += ("\t\t" + name + "_LABEL: " + name.lower() + "();\n")

	# end those puny braces
	label_cpp += "};"
	switch_cpp += "\t}\n}"

	verifyAndReplace(VM_OPCODES_FILE, opcodes_cpp)
	verifyAndReplace(VM_SWITCH_FILE, label_cpp+switch_cpp)

	
	