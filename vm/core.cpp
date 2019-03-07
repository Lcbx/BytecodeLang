
#include "common.h"
#include "core.h"

// generated file, see opcodes.py
void Interpreter::execute_switch(){
	static const void* labels[] = {&&NO_OP_LABEL, &&OP_NONE_LABEL, &&OP_TRUE_LABEL, &&OP_FALSE_LABEL, &&OP_INT_LABEL, &&OP_FLOAT_LABEL, &&OP_STRING_LABEL, &&OP_LOAD_LABEL, &&OP_STORE_LABEL, &&OP_POP_LABEL, &&OP_JUMP_LABEL, &&OP_JUMP_IF_LABEL, &&OP_JUMP_IF_FALSE_LABEL, &&OP_EQ_LABEL, &&OP_NEQ_LABEL, &&OP_LT_LABEL, &&OP_LTE_LABEL, &&OP_GT_LABEL, &&OP_GTE_LABEL, &&OP_ADD_LABEL, &&OP_SUB_LABEL, &&OP_MUL_LABEL, &&OP_DIV_LABEL, &&OP_NEG_LABEL, &&OP_PRINT_LABEL, &&OP_PRINT_CHAR_LABEL, &&OP_SHOW_STACK_LABEL, };
	uchar opcode = 0;
	#define DISPATCH() opcode = code.next(); if(!code.ended){ goto *labels[opcode];} else return;
	#define PRINT_OP() DEBUG(std::cout << "OP " << code.pointer << " : " << +code.current() << "   ";)
	DISPATCH()
	while(1){
		NO_OP_LABEL: PRINT_OP() no_op(); DISPATCH()
		OP_NONE_LABEL: PRINT_OP() op_none(); DISPATCH()
		OP_TRUE_LABEL: PRINT_OP() op_true(); DISPATCH()
		OP_FALSE_LABEL: PRINT_OP() op_false(); DISPATCH()
		OP_INT_LABEL: PRINT_OP() op_int(); DISPATCH()
		OP_FLOAT_LABEL: PRINT_OP() op_float(); DISPATCH()
		OP_STRING_LABEL: PRINT_OP() op_string(); DISPATCH()
		OP_LOAD_LABEL: PRINT_OP() op_load(); DISPATCH()
		OP_STORE_LABEL: PRINT_OP() op_store(); DISPATCH()
		OP_POP_LABEL: PRINT_OP() op_pop(); DISPATCH()
		OP_JUMP_LABEL: PRINT_OP() op_jump(); DISPATCH()
		OP_JUMP_IF_LABEL: PRINT_OP() op_jump_if(); DISPATCH()
		OP_JUMP_IF_FALSE_LABEL: PRINT_OP() op_jump_if_false(); DISPATCH()
		OP_EQ_LABEL: PRINT_OP() op_eq(); DISPATCH()
		OP_NEQ_LABEL: PRINT_OP() op_neq(); DISPATCH()
		OP_LT_LABEL: PRINT_OP() op_lt(); DISPATCH()
		OP_LTE_LABEL: PRINT_OP() op_lte(); DISPATCH()
		OP_GT_LABEL: PRINT_OP() op_gt(); DISPATCH()
		OP_GTE_LABEL: PRINT_OP() op_gte(); DISPATCH()
		OP_ADD_LABEL: PRINT_OP() op_add(); DISPATCH()
		OP_SUB_LABEL: PRINT_OP() op_sub(); DISPATCH()
		OP_MUL_LABEL: PRINT_OP() op_mul(); DISPATCH()
		OP_DIV_LABEL: PRINT_OP() op_div(); DISPATCH()
		OP_NEG_LABEL: PRINT_OP() op_neg(); DISPATCH()
		OP_PRINT_LABEL: PRINT_OP() op_print(); DISPATCH()
		OP_PRINT_CHAR_LABEL: PRINT_OP() op_print_char(); DISPATCH()
		OP_SHOW_STACK_LABEL: PRINT_OP() op_show_stack(); DISPATCH()
}}