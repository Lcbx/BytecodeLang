
#include "common.h"
#include "core.h"

// generated file, see opcodes.py
void Interpreter::execute_switch(){
	DEBUG(std::cout << "in execute\n";)
	static const void* labels[] = {&&NO_OP_LABEL, &&OP_NONE_LABEL, &&OP_TRUE_LABEL, &&OP_FALSE_LABEL, &&OP_INT1_LABEL, &&OP_INT2_LABEL, &&OP_INT4_LABEL, &&OP_FLOAT_LABEL, &&OP_STRING_LABEL, &&OP_LOAD_LABEL, &&OP_STORE_LABEL, &&OP_POP_LABEL, &&OP_JUMP_LABEL, &&OP_JUMP_IF_LABEL, &&OP_JUMP_IF_FALSE_LABEL, &&OP_EQ_LABEL, &&OP_NEQ_LABEL, &&OP_LT_LABEL, &&OP_LTE_LABEL, &&OP_GT_LABEL, &&OP_GTE_LABEL, &&OP_ADD_LABEL, &&OP_SUB_LABEL, &&OP_MUL_LABEL, &&OP_DIV_LABEL, &&OP_NEG_LABEL, &&OP_PRINT_LABEL, &&OP_PRINT_CHAR_LABEL, &&OP_SHOW_STACK_LABEL, &&OP_END_LABEL, };
	uchar opcode = 0;
	#define DISPATCH() opcode = code.next(); goto *labels[opcode];
	DISPATCH()
	while(false){
		NO_OP_LABEL: no_op(); DISPATCH()
		OP_NONE_LABEL: op_none(); DISPATCH()
		OP_TRUE_LABEL: op_true(); DISPATCH()
		OP_FALSE_LABEL: op_false(); DISPATCH()
		OP_INT1_LABEL: op_int1(); DISPATCH()
		OP_INT2_LABEL: op_int2(); DISPATCH()
		OP_INT4_LABEL: op_int4(); DISPATCH()
		OP_FLOAT_LABEL: op_float(); DISPATCH()
		OP_STRING_LABEL: op_string(); DISPATCH()
		OP_LOAD_LABEL: op_load(); DISPATCH()
		OP_STORE_LABEL: op_store(); DISPATCH()
		OP_POP_LABEL: op_pop(); DISPATCH()
		OP_JUMP_LABEL: op_jump(); DISPATCH()
		OP_JUMP_IF_LABEL: op_jump_if(); DISPATCH()
		OP_JUMP_IF_FALSE_LABEL: op_jump_if_false(); DISPATCH()
		OP_EQ_LABEL: op_eq(); DISPATCH()
		OP_NEQ_LABEL: op_neq(); DISPATCH()
		OP_LT_LABEL: op_lt(); DISPATCH()
		OP_LTE_LABEL: op_lte(); DISPATCH()
		OP_GT_LABEL: op_gt(); DISPATCH()
		OP_GTE_LABEL: op_gte(); DISPATCH()
		OP_ADD_LABEL: op_add(); DISPATCH()
		OP_SUB_LABEL: op_sub(); DISPATCH()
		OP_MUL_LABEL: op_mul(); DISPATCH()
		OP_DIV_LABEL: op_div(); DISPATCH()
		OP_NEG_LABEL: op_neg(); DISPATCH()
		OP_PRINT_LABEL: op_print(); DISPATCH()
		OP_PRINT_CHAR_LABEL: op_print_char(); DISPATCH()
		OP_SHOW_STACK_LABEL: op_show_stack(); DISPATCH()
		OP_END_LABEL: op_end();
	}
}