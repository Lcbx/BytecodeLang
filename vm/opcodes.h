
#pragma once
#include "common.h"

// generated header, see opcodes.py
const uchar NO_OP = 0;
const uchar OP_NONE = 1;
const uchar OP_TRUE = 2;
const uchar OP_FALSE = 3;
const uchar OP_INT1 = 4;
const uchar OP_INT2 = 5;
const uchar OP_INT4 = 6;
const uchar OP_FLOAT = 7;
const uchar OP_STRING = 8;
const uchar OP_LOAD = 9;
const uchar OP_STORE = 10;
const uchar OP_POP = 11;
const uchar OP_JUMP = 12;
const uchar OP_JUMP_IF = 13;
const uchar OP_JUMP_IF_FALSE = 14;
const uchar OP_EQ = 15;
const uchar OP_NEQ = 16;
const uchar OP_LT = 17;
const uchar OP_LTE = 18;
const uchar OP_GT = 19;
const uchar OP_GTE = 20;
const uchar OP_ADD = 21;
const uchar OP_SUB = 22;
const uchar OP_MUL = 23;
const uchar OP_DIV = 24;
const uchar OP_NEG = 25;
const uchar OP_PRINT = 26;
const uchar OP_PRINT_CHAR = 27;
const uchar OP_SHOW_STACK = 28;
const uchar OP_END = 29;
