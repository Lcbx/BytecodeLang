## TODO.md
This is where I put my pending tasks/ ideas. I could keep around what has been done as cossed-out text, so I can be reminded of the feature list, but it's quite simple right now so...

#### bugs
- vm_simulation crash on wrong filepath (add an error message)

#### compiler
- support late binding of variables and functions
- support arrays
- enhance support objects (hybrid approach right now)
- make compiling smarter and optimized
- enhance variable assignation and loading
- add more control structures (for, do/while (?), etc)
- add iterables (IEnumerable in C#) and functionnal programing

#### language design
- support basic data structures (at least arrays !)
- support functions  
	make functions be both objects and constructors  
	'declare' the object's fields when the function is called  
``` CoffeeScript
def A() 
	let b = (...)
	var c = (...)

let obj = A()
obj.b # generates error
obj.c # returns c 
```  
The **lisibility** is still good/better, it allows for **multiple return values**,
you **don't have to refactor code into classes**. I think it would foster more **behaviour-oriented** coding.
**BUT** it does not mesh well with **inheritance**, or at least makes it verbose - you have to redeclare properties and functions.
(in the proposed code, let makes a variable go on the stack, var puts it in a heap object; the maximum number of fields can be known at compiled time).
would duck-typing still work / be usefull ?
- handle null like an empty list.  
the goal is to make null the less cancerous as possible.  
get rid of it, and tell people to use an empty list, which itself is going to be implemented as a sentinel value that can be converted to a list when list functions are called on it  
(?) leave a way to check for missing data using if statement (if a then a.b else ... )
- (?) support generator expressions (enumerables & co) 
- (?) support chained comparisons x<y<z

- what about using objects' members as parameters for functions automagically :
``` CoffeeScript
def A() 
	var b
	var c

def D(b,c,e)
	...

let e
let obj = A()
D(obj, e) # uses b c computed in A()
```
- make order of parameters not syntaxically relevant (+ allow unused / redondant parmeters ?)
- allow closures ? ( = hidden function states ) + if not still, allow using function references but disallow returning a function itself
- make a Callable type or support function as a native type?
- while and for loop considered enumerable expressions
- enumerable treated as so until an attempt at accessing an index, then it is converted to list automatically
- use an async keyword where a function call is started on another thread,Task-like (+ use an await keyword to get their results ?)

### technical ideas
- implement Nan tagging : https://github.com/wren-lang/wren/blob/master/src/vm/wren_value.h
- test equality strictly based on type and object data. if an object is composed of other objects, check if the pointer is the same and, if it isn't, test if the object data is the same.
- (?) only use dynamic allocation of arrays as hardcoded data structure, then implement maps, vectors and lists as "normal" classes that are loaded  on vm start - simpler vm and more flexible BUT that makes for a lot of homemade code and potential bugs
- add simple tail-call optimisation : if a function returns a funtion call to itself, replace the call by a goto
``` CoffeeScript
def f(expr1, ...)
	doStuff()
	return  f(expr2, ...)
# becomes :
# push compute(expr1), ...  
# label_1 : doStuff  
# put expr2 in expr1's place in stack, ...  
# goto label_1
```
- (?) inline every function call, then compress bytecode with LZW, and decompress on the fly ? that could make the program take less space both in file and in RAM during execution. See [this](http://www.cplusplus.com/articles/iL18T05o) for a performance-oriented implementation.