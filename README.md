## What's this ?
BytecodeLang (name is temporary) is a language i've been working on and off since mid-2018.  
It consists of a **stack-based VM in c++** and a **compiler in Python** (with no external libraries in either case); a few tools (an [assembly-like compiler](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/assembly_compiler.py), a [disassembler](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/disassembler.py) and a [vm simulator](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/vm_simulator.py)) are developped concurrently to help debugging. 
Right now it is at the "slightly smart calculator" stage.

*note :*  to ensure that the bytecodes match between the compiler and vm, i use a [script](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/opcodes.py) that generates a [c++ header file](https://github.com/Lcbx/BytecodeLang/blob/master/vm/opcodes.h) based on the compiler definitions. In fact now it also generates the dispatch table for the interpreter using [computed gotos](https://github.com/Lcbx/BytecodeLang/blob/master/vm/core.cpp).

### Why c++ and Python?
A language is supposed to be fast and efficient, but all software should be as simple and readable as can be.  
I chose c++ for the vm for its performance, readability (less verbose than c) and access to the standard libray : i don't want to start from the ground up (implementing strings, dictionnaries, etc) because the code would probably be less efficient and a source of potential bugs.  
However, since i intend programs to be shipped as bundles of bytecode, the compiler does not have to be that performant. I chose Python because it is an experimentation-friendly, high-level language that i love.

## Where is it going ?
The eventual goal is to make a class-based, duck-typed, heavily python-inspired language (syntactically meaningfull indentation, native lists and dictionnaries, range-based for) with manual memory management. It would be similar in principle and implementation but hopefully simpler and less verbose than [munificient's wren](https://github.com/wren-lang/wren) (from whom i borrow quite heavily otherwise). I can't see why new languages keep those redondant, clutter-inducing curly braces. 

Ex:
``` CoffeeScript
class Bird
    # members are not defined in constructor. no static fields :
    # global state belongs at script level, not in a class
    wingspan = 1
    # c++ style constructor, with automatic initialisation (based on variable name) 
    Bird(wingspan)
    # declaring a function uses the def keyword
    def fly()
        # access to members will be made with a @, faster than "self." and readable
        return @wingspan * 40
    def caw()
        # 'no unecessary chatter' philosophy : print, log, input and output use << (print by default)
        << "caaaw"

class Hawk(Bird)
    wingspan = 1.3
    def caw()
        << "<insert hawk sound here>"

class Plane
    def fly()
        return 150

# when not a class member, variables and functions must be declared with "var" and "def"
var test = [Bird(), Hawk(), Plane()]
for obj in test
    # string interpolation and conversion are implicit (i find it terse and expresive)
    << "object flying at " obj.fly() "mph"
```

### Why no garbage collection?
* Firstly, it's a problem that has been tackled a billion times and is not sexy (to me at least),
* if objects created in a scope are destroyed when leaving said scope (except those in a return statment which are transfered to the upper scope), i think most cases are handled,
* i feel that it can be retrofitted easily (if needed) anyway,
* frankly, a modern scripted language with manual memory management sounds fun,
* so why bother?

### How do you intend to make classes support duck-typing?
Good question!

I intend to make objects arrays of values that begin with a pointer to the class it implement. The classes themselves will each have a dictionary of functions which will "know" at compile time the offsets of a class instance's members, so a class function should be fast when accessing the object's members.

Functions with the same signature (name, number of arguments, and also the arguments' types if specified) have the same hash number ; that's the magic that allows duck typing.

This, however, means there will be a fixed amount of indirection when an outsider function accesses an object's member value since it will not know the correct offset ; the object's members will not be accessible directly (there will be getters and setters functions generated automatically).

### What plans do you have once the basic stuff is done ?
The most important feature to make a language grow would be a good  **import** system : importing scripts from the language will be one of the first priorities. The simple way of doing it would be to interpret an imported script (and *not* its' bytecode as the bindings of functions' names and hash would be lost) at the same level as the main script. Since the language is not intended to be library-heavy and the compilation will be made in a single pass, there shouldn't be any problem. A better way would be to leave some compilation-relevant stuff in a file seprate from the bytecode to allow using it as library.
Coming up after that will be **loading wrapped-up c++ dlls**.
That would allow us to use all those fast and powerfull c++ libraries. It would also be cool to have a built-in utility tool like pip that'd dowload missing imports automatically from it's github repo. A man can dream.
 
