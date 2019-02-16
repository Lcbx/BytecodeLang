## What is this ?

This is a bytecode-based interpreted language that i have worked on and off since mid-2018. It is made of an interpreter VM  in c++ and a compiler in python.
Right now the interpreter can load and interpret various instructions and should be np-complete. The compiler is not really there yet.

*note :*  to ensure that the bytecode is guaranteed to match between the compiler and interpreter, i use a script ([opcodes.py](https://github.com/Lcbx/BytecodeLang/blob/master/opcodes.py)) that generates a c++ header file (opcodes.h) from the compiler definitions. Though i should separate the compiler and interpreter source files one of these days for clarity.

## Where is it going ?

The eventual goal is to make a class-based, duck-typed, heavily python-inspired language (syntactically meaningfull indentation, native lists and dicts, range-based for) with manual memory management. It would be similar in principle and implementation but hopefully simpler and less verbose than [munificient's wren](https://github.com/wren-lang/wren).

Ex:
``` dart
class Bird
	//implicit type of int
	wingspan = 1
	//creating an Object is as simple as calling the class name like a function
	mate = Bird()
	//declaring a function
	fly()
		//access to members will be made with a @, faster than "self." and readable
		return @wingspan * 40
	caw()
		//with a 'no unecessary chatter' philosophy, print, log, input and output will be a similar to c++ cout operators
		<< "caaaw"

class Hawk(Bird)
	wingspan = 1.3
	caw()
		<< "<insert hawk sound here>"

class Plane
	fly()
		return 150
		
// when out of a class, variables and functions must be declared with "var" and "func"
var test = [Bird(), Hawk(), Plane()]
for obj in test
	// string interpolation and conversion are implicit
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

I intend to make objects arrays of values with a header that consists of  a pointer to the class it implement. The classes themselves will have dictionaries of internal functions which will "know" at compile time the offsets of a class instance's members, so a class function should be fast when accessing the object's members.

 Functions with the same signature (name, number of arguments, and also the arguments' types if specified) have the same hash number ; that's the magic that allows duck typing.

This, however, means there will be a fixed amount of indirection when an outsider function accesses an object's member value since it will not know the correct offset ; the object's members will not be accessible directly (there will be getters and setters functions generated automatically).

### What plans do you have once the basic stuff is done ?
The most important feature to make a language grow would be a good  **import** system : importing scripts from the language will be one of the first priorities. The simple way of doing it would be to interpret an imported script (and *not* its' bytecode as the bindings of functions' names and hash would be lost) at the same level as the main script. Since the language is not intended to be library-heavy and the compilation will be made in a single pass, there shouldn't be any problem.
Coming up after that will be **loading wrapped-up c++ dlls**.
That would allow us to use all those fast and powerfull c++ libraries. It would also be cool to have a built-in utility tool like pip that'd dowload missing imports automatically from it's github repo. A man can dream.

 On a lighter note, i think that implementing **double dispatch** would be fun and  easy as adding syntactic sugar like this : 
``` dart
// code to desugar
func collide(a, b) : collide(a : Hawk, b) or collide(a : Plane, b : Bird)

// resulting code
func collide(a,b)
	if a : Hawk
		return collide_Asteroid(a, b)
	if a : Plane and b : Bird
		return collide_Asteroid(a, b)
	return Error("no implementation for a : " type(a) " and b: " type(b))
```
However, at least at the beginning, types will not track the inheritance chain : a Hawk may be a Bird, but i don't think i'll bother making a check on a type's ancestry, so that type of dispatch may be clunky. 

Also, **multiple inheritence** should be easy to add since every class will have it's own version of a function ; i don't think diamond inheritance will be permitted though.
``` dart
// that would be Awesome !
class Hawk(Bird,Canivore)
	pass
// "Error diamond inheritance : Bird and BirdOfPrey both are Bird" 
class Howl(Bird, BirdOfPrey)
	pass
```
 
