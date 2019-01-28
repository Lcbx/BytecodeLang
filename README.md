## What is this ?
this is a bytecode based interpreted language that i have worked on and off since mid-2018
It is made of an interpreter VM  in c++ and a compiler in python
right now the interpreter can charge and interpret various instructions and should be np-complete,
and the compiler is not really there yet

### note 
so bytecode is guaranteed to match between the compiler and interpreter, i use a script (opcodes.py) that generates a c++ header file (opcodes.h) from the compiler definitions
though i should separate the compiler and interpreter source one of these days for clarity