### FIX :
- refactor opcodes.py : right now 2 files are generated at once, it's unreadable
- still in opcode.py : add the option to go back to a big switch (like in early versions) instead of computed gotos

#### bugs
- make more code tests to hunt for those !

#### compiler
- produce instructions (WIP)
- make better variable assignation and loading
- support late binding of variables and functions declarations
- add more control structures (if, while, for, etc) (WIP)
- make compiling smarter and optimized

#### language
- support functions
- support basic data structures
- support classes
- implement Nan tagging : https://github.com/wren-lang/wren/blob/master/src/vm/wren_value.h

### technical ideas
- test equality strictly based on type and object data. if an object is composed of other objects, check if the pointer is the same and, if it isn't, test if the object data is the same.
- (?) only use dynamic allocation of arrays as hardcoded data structure, then implement maps, vectors and lists as "normal" classes that are loaded  on vm start - simpler vm and more flexible BUT that makes for a lot of homemade code and potential bugs
