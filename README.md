## What's this ?
BytecodeLang (name is temporary) is a language I've been working on and off since mid-2018.  
It consists of a **[compiler in Python](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/compiler.py)** that and a custom **[stack-based bytecode interpreter/VM in c++](https://github.com/Lcbx/BytecodeLang/blob/master/vm/core.h)** (with no external libraries in either case).
Popular examples of this approach are [C# and it's CLI/CLR](https://en.wikipedia.org/wiki/Common_Intermediate_Language) or [Java and it's Java Bytecode/JVM](https://en.wikipedia.org/wiki/Java_virtual_machine).
  
A few tools (an [assembly-like compiler](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/assembly_compiler.py), a [disassembler](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/disassembler.py), a [vm simulator](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/vm_simulator.py), and a [test laucher](https://github.com/Lcbx/BytecodeLang/blob/master/LaunchTests.py)) are developped concurrently to help debugging.
To ensure that the bytecodes match between the compiler and vm, a [script](https://github.com/Lcbx/BytecodeLang/blob/master/compiler/opcodes.py) generates a [c++ header file](https://github.com/Lcbx/BytecodeLang/blob/master/vm/opcodes.h) based on the compiler definitions.
In fact now it also generates the [dispatch table](https://github.com/Lcbx/BytecodeLang/blob/master/vm/core.cpp) for the interpreter.
The interpreter is a bit of a second class citizen since the language is developped with a vm simulator, and changes are then back-propagated to c++.
  
Right now it is at the "calculator with some imperative instructions" stage.  
Please note that this is *not* an attempt at creating a production-ready language.

### Example (actual state of language)
```CoffeeScript
def n = 10

def a = 0
def b = 1
def c = 0
while n > 0
	c = a + b
	b = a
	a = c
	n = n -1

# the Nth number of the suite
print a
```
see [fibonacci.byte](https://github.com/Lcbx/BytecodeLang/blob/master/tests/fibonacci.byte)


### Why c++ and Python?
A language is supposed to be fast and efficient, but all software should be as simple and readable as can be.  
I use c++ for the vm for its performance, readability (less verbose than c) and access to the standard libray : to start from the ground up (implementing strings, dictionnaries, etc) would make the project considerably bigger, probably less performant, and be a source of potential bugs.  
I chose Python in the compiler because it's a high-level, well-known language and performance isn't really important for a single-pass compiler.

## Where is it going ?
The moving goalpost here is to make a python-ish (syntactically meaningfull indentation, native lists and dictionnaries, range-based for), lightly object-oriented (to allow duck-type-ness) language, with an emphasis on manipulating data using functional programming (map/select, filter/where, ...), and possibly manual memory management (if needed). The development is inspired by [munificient's wren](https://github.com/wren-lang/wren) and [tsoding's Porth](https://github.com/tsoding/porth).

### Example (not actual state of language)
``` CoffeeScript
# functions and classes are indistinguishable :
# a function is a constructor for it's results/properties, 
# and those can be modified by calling it's methods (not truly functional I know)
def Bird(wingspan)
    
    # no static fields : global state does not belong in a class
    var speedPerWingspan = 40
    
    # declaring a method uses the def keyword
    def fly()
        # access to members will be made with a '.', faster than "self." and still readable
        return .wingspan * .speedPerWingspan
    
    def caw()
        # 'no unecessary chatter' philosophy : print, log, input and output use << and >> (print by default)
        << "caaaw"

# multiple inheritance could be a thing but diamond inheritance will probably be disallowed
def Hawk() : Bird(1.3)
    def caw()
        << "<insert hawk sound here>"

def Plane()
    def fly()
        return 150

# when not a class member, variables and functions must be declared with "var" and "def" 
var test = [Bird(1), Hawk(), Plane()]
for obj in test
    # string interpolation and conversion are implicit
    << "object flying at " obj.fly() "mph"

# delete statement (similar to c++ delete)
del var1 var2
```

### How do you intend to make classes support duck-typing?
Good question!

Objects would be arrays of values that begin with a pointer to the class it implement. The classes themselves will each have a dictionary of functions which will "know" at compile time the offsets of a class instance's members, so a class function should be fast when accessing the object's members.

Functions/methods with the same signature (name, number of arguments, and also the arguments' types if specified) have the same hash number ; that's the magic that allows duck typing.

This, however, means there will be a fixed amount of indirection when an outsider function accesses an object's member value since it will not know the correct offset ; the object's members will not be accessible directly (there will be getters and setters functions generated automatically).


### Why no garbage collection?
* Firstly, it's a problem that has been tackled a billion times and is not sexy (to me at least),
* if objects created in a scope are destroyed when leaving said scope (except those in a return statment which are transfered to the upper scope), I think most cases are handled,
* it can be retrofitted easily (if needed) anyway,
* frankly, a modern scripted language with manual memory management sounds fun,
* so why bother?

### What plans do you have once the basic stuff is done ?
The most important feature to make a language grow would be a good  **import** system : importing scripts from the language will be one of the first priorities. The simple way of doing it would be to interpret an imported script (and *not* its' bytecode as the bindings of functions' names and hash would be lost) at the same level as the main script. Since the language is not intended to be library-heavy and the compilation will be made in a single pass, there shouldn't be any problem. A better way would be to leave some compilation-relevant stuff in a file seprate from the bytecode to allow using it as library.
Coming up after that will be **loading wrapped-up c++ dlls**.
That would allow us to use all those fast and powerfull c++ libraries. It would also be cool to have a built-in utility tool like pip that'd dowload missing imports automatically from it's github repo. A man can dream.

## Addendum : The balance between expressivity, readability and familiarity
* **expressivity** is the collection of design decisions that allow the language to **do more with less** code.  
Dynamic-typed languages are more expressive than static ones since you don't have to write a type near each variable definitions, so are functionnal languages with their versatile higher-order functions (most imperative languages today have introduced at least a subset of those).
* **readability** is what allows another programmer to **intuit the logic** behind a piece of code.  
The _goto_ statement was an early member of programming languages that allowed a lot of control over the program logical flow, but was later removed because the produced "spaguetti" code was unmaintainable. Statically-typed languages are deemed more readable (and so maintainable) than dynamic ones since types are explicit ; on top of that type-safety is ensured and therefore a lot of errors are caught before runtime. As a firm advocate of duck-typing, I do not believe the perks are worth the cost in boilerplate code and the arbitrary, overbearing rules that come with static typing.
* Lastly, **familiarity** is how **easy to pick-up** the language is,  
whether it's by being close to another language or more intuitive to non-programmers. This notion is close to readability, but not the exact same : familiarity is about ensuring the comprehension of a given piece of code through similarities to other languages and/or mathematical expressions the reader might have seen.
For example, the mathematical statement `a = 1+2+3` would be just the same in Python, but would be translated to `(def a (+ 1 2 3))` in the functionnal language Clojure. Now if you know why it is that way, i'm sure you admire the idea behind the language. But let's agree that it's not intuitive at all. Familiarity is a good crutch to make a new language : by following or building on established rules and notions, it can ensure that the person learning it won't be lost. However, the desire to keep your language familiar to possible users can get in the way of any original design idea you have. Please consume in moderation.
 
