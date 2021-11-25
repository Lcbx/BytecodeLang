
#pragma once
#include "common.h"

// generated header, see opcodes.py
const Byte NO_OP = 0;
const Byte OP_NONE = 1;
const Byte OP_TRUE = 2;
const Byte OP_FALSE = 3;
const Byte OP_INT1 = 4;
const Byte OP_INT2 = 5;
const Byte OP_INT4 = 6;
const Byte OP_FLOAT = 7;
const Byte OP_STRING = 8;
const Byte OP_LOAD = 9;
const Byte OP_STORE = 10;
const Byte OP_POP = 11;
const Byte OP_JUMP = 12;
const Byte OP_JUMP_IF = 13;
const Byte OP_JUMP_IF_FALSE = 14;
const Byte OP_EQ = 15;
const Byte OP_NEQ = 16;
const Byte OP_LT = 17;
const Byte OP_LTE = 18;
const Byte OP_GT = 19;
const Byte OP_GTE = 20;
const Byte OP_ADD = 21;
const Byte OP_SUB = 22;
const Byte OP_MUL = 23;
const Byte OP_DIV = 24;
const Byte OP_NEG = 25;
const Byte OP_PRINT = 26;
const Byte OP_SHOW_STACK = 27;
const Byte OP_END = 28;
