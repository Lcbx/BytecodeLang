operations = [

"NO_OP",

"OP_NONE",
"OP_TRUE",
"OP_FALSE",
"OP_INT",
"OP_FLOAT",
"OP_STRING",

"OP_LOAD",
"OP_STORE",
"OP_POP",
"OP_COPY",

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

]

for n, name in enumerate(operations):
	# declares opcodes in python
	exec( name + " = " + str(n) )

if __name__ == "__main__":

	VM_FILE = "../vm/opcodes.h"

	# builds cpp file used in virtual machine
	cpp = "#pragma once\n#include \"common.h\"\n\n\n// generated header, see opcodes.py\n"
	for n, name in enumerate(operations):
		cpp += ("const uchar " + name + " = " + str(n) + ";\n")

	# verify if opcodes are up to date
	file = open(VM_FILE,'r')
	content = file.read()
	file.close()
	# if they aren't, changes the file content
	if content != cpp:
		file = open(VM_FILE,'w')
		file.write(cpp)
		file.close()
		print("opcodes updated !")
	