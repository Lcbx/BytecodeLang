#pragma once
#include "common.h"


// generated header, see opcodes.py
const uchar NO_OP = 0;
const uchar OP_NONE = 1;
const uchar OP_TRUE = 2;
const uchar OP_FALSE = 3;
const uchar OP_INT = 4;
const uchar OP_FLOAT = 5;
const uchar OP_STRING = 6;
const uchar OP_LOAD = 7;
const uchar OP_STORE = 8;
const uchar OP_POP = 9;
const uchar OP_COPY = 10;
const uchar OP_JUMP = 11;
const uchar OP_JUMP_IF = 12;
const uchar OP_JUMP_IF_FALSE = 13;
const uchar OP_EQ = 14;
const uchar OP_NEQ = 15;
const uchar OP_LT = 16;
const uchar OP_LTE = 17;
const uchar OP_GT = 18;
const uchar OP_GTE = 19;
const uchar OP_ADD = 20;
const uchar OP_SUB = 21;
const uchar OP_MUL = 22;
const uchar OP_DIV = 23;
const uchar OP_NEG = 24;
const uchar OP_PRINT = 25;
const uchar OP_PRINT_CHAR = 26;
const uchar OP_SHOW_STACK = 27;
