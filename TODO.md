### FIX :
- string prints have twice the first char in interpreter

#### flesh out the compiler
 - load floats
- produce instructions

#### flesh out the language
- support functions
- support classes
- support data structures

### technical ideas
- concern : we can have contiguous memory through STL in vectors and in classes, but map seems hard...
- only use dynamic allocation of arrays as hardcoded data structure, then implement maps, vectors and lists as "normal" classes that are loaded  on vm start (?)
- 1.5 pass : parse and identify statements in one pass,
but each statement is recursive from the one before within a scope,
so some analysis on type and variable use can be done.
code gets generated on return of recursion, so in reverse order.
``` dart
// Exemple :
statement1
if condition
	statement2
	statement3
statement4
// becomes as a recursive function call :
statement1 				// 5th to generate code
	if someCondition 		// 3rd, will wait for statement4
		 statement2 		// 2nd
			 statement3 	// 1st
	statement4 			// 4th
```
- errors during parsing : make parsing wrapper that catches all errors and propagates them as array in return statements so that at end of parsing we have a maximum of relevant info
