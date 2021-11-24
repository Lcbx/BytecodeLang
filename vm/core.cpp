
#include "common.h"
#include "core.h"

// generated file, see opcodes.py
void Interpreter::execute_switch(){
	DEBUG(std::cout << "in execute\n";)
	uchar opcode = 0;
	while(opcode != OP_END){
		opcode = code.next();
		switch(opcode){
			case NO_OP: no_op(); break;
			case OP_NONE: op_none(); break;
			case OP_TRUE: op_true(); break;
			case OP_FALSE: op_false(); break;
			case OP_INT1: op_int1(); break;
			case OP_INT2: op_int2(); break;
			case OP_INT4: op_int4(); break;
			case OP_FLOAT: op_float(); break;
			case OP_STRING: op_string(); break;
			case OP_LOAD: op_load(); break;
			case OP_STORE: op_store(); break;
			case OP_POP: op_pop(); break;
			case OP_JUMP: op_jump(); break;
			case OP_JUMP_IF: op_jump_if(); break;
			case OP_JUMP_IF_FALSE: op_jump_if_false(); break;
			case OP_EQ: op_eq(); break;
			case OP_NEQ: op_neq(); break;
			case OP_LT: op_lt(); break;
			case OP_LTE: op_lte(); break;
			case OP_GT: op_gt(); break;
			case OP_GTE: op_gte(); break;
			case OP_ADD: op_add(); break;
			case OP_SUB: op_sub(); break;
			case OP_MUL: op_mul(); break;
			case OP_DIV: op_div(); break;
			case OP_NEG: op_neg(); break;
			case OP_PRINT: op_print(); break;
			case OP_SHOW_STACK: op_show_stack(); break;
			case OP_END: op_end(); break;
			default: break;
		}
	}
}