#define _SCL_SECURE_NO_WARNINGS
#include <stack>
#include <vector>
#include <fstream>
#include "Value.cpp"
#include "opcodes.h"


class ByteCode {
public:

	const Int max;
	const uchar* bytes;
	Int pointer = 0;

	ByteCode(uchar* s, Int length) : bytes(s), max(length) {
		DEBUG(
			for(int i=0; i<length; i++)
					std::cout<< ((int) s[i]) << " ";
				std::cout<<"\n";
		)
	}
	uchar next() { return pointer<=max ? bytes[pointer++] : 0; }
	template<typename T> T read() {
		T result = *(T*)(bytes + pointer);
		pointer += sizeof(T);
		return result;
	}
	char peek() { return bytes[pointer]; }
	void reset() { pointer = 0; }
	void jump(Int i) { pointer += i; }
};



class Interpreter {
public:
	std::stack<Variable> stack;
	std::deque<Variable> registers;
	Interpreter() : registers(0) {} //max 256

	inline Variable& top() { return stack.top(); }
	Variable pop() { Variable var(top()); stack.pop(); return var; }
	template<typename T> void push(T arg) { stack.emplace<Variable>(arg); }
	

	void execute(uchar* s, Int length) {
		ByteCode b(s, length);
		execute(b);
	}

	void executeFromFile(String fileName) {
		std::ifstream in(fileName, std::ios::binary);
		std::vector<uchar> buffer((
			std::istreambuf_iterator<char>(in)),
			(std::istreambuf_iterator<char>()));
		buffer.shrink_to_fit();
		execute(buffer.data(), buffer.size());
	}



	void execute(ByteCode code) {
		while (code.pointer < code.max) {

			DEBUG(std::cout << "OP " << code.pointer;)
			uchar opcode = code.next();
			DEBUG(std::cout << " : " << +opcode << "   ";)
			
			// This is where magic happens
			switch (opcode) {

			case NO_OP: { 
				DEBUG(std::cout << "NOOP " << std::endl;)
				break;
			}

			case OP_NONE: {
				push( None_ );
				DEBUG(std::cout << "none " << std::endl;)
				break;
			}

			case OP_TRUE: {
				push( True_ );
				DEBUG(std::cout << "true " << std::endl;)
				break;
			}

			case OP_FALSE: {
				push( False_ );
				DEBUG(std::cout << "false " << std::endl;)
				break;
			}

			case OP_INT: {
				push(code.read<Int>());
				DEBUG(std::cout << "int " << top().toString() << std::endl;)
				break;
			}
			
			case OP_FLOAT: {
				push(code.read<Float>());
				DEBUG(std::cout << "float " << top().toString() << std::endl;)
				break;
			}
			
			case OP_STRING: {
				String* s = new String();
				DEBUG(std::cout << "string ";)
				for (char c = code.next(); c != 0; c = code.next()) {
					*s += c;
					DEBUG(std::cout << c << std::flush;)
				}
				DEBUG(std::cout << std::endl;)
				push( s );
				break;
			}

			
			case OP_LOAD: {
				uchar address = code.read<uchar>();
				Variable var = registers[address];
				// compiler says no copy construction #WorkAroundFTW
				push(None_);
				Variable::copy(var, top());
				DEBUG(std::cout << "LOAD " << +address << " : " << var.toString() << std::endl;)
				break;
			}

			case OP_STORE: {
				uchar address = code.read<uchar>();
				Variable var = pop();
				registers[address] = var;
				DEBUG(std::cout << "STORE " << +address << " : " << var.toString() << std::endl;)
				break;
			}

			case OP_POP: {
				pop();
				DEBUG(std::cout << "POP" << std::endl;)
				break;
			}
			

			case OP_JUMP_IF: {
				Variable condition = pop();
				if (condition.type == True_) {
					Short distance = code.read<Short>();
					code.pointer += distance;
					DEBUG(std::cout << "jump " << +distance << std::endl;)
				}
				break;
			}

			case OP_EQ: {
				Variable a = pop();
				Variable b = pop();
				if (a.type == Int_ && b.type == Int_)
					push(a.content.asInt + b.content.asInt);
				else if ((a.type == Float_ || a.type == Int_) && (b.type == Float_ || b.type == Int_)) {
					Float val_a = a.type == Float_ ? a.content.asFloat : (Float)a.content.asInt;
					Float val_b = b.type == Float_ ? b.content.asFloat : (Float)b.content.asInt;
					push(val_a == val_b);
				}
				else if (a.type == String_ && b.type == String_) {
					push(a.toString() == b.toString());
				}
				////////////
				// INSERT COMP OF ARRAYS AND OBJ HERE
				////////////
				else if (a.type == b.type) push(True_); // None == None, False == False, etc
				else push(False_);
				DEBUG(std::cout << a.toString() << " == " << b.toString() << " => " << top().toString() << std::endl;)
				break;
			}

#define BINARY(operator, error) {	\
		Variable b = pop();			\
		Variable a = pop();			\
		if (a.type == Int_ && b.type == Int_) 						\
			push(a.content.asInt operator b.content.asInt); 		\
		else if(a.type == Float_ && b.type == Int_)					\
			push(a.content.asFloat operator (Float)b.content.asInt);\
		else if(a.type == Int_ && b.type == Float_)					\
			push((Float)a.content.asInt operator b.content.asFloat);\
		else error													\
		DEBUG(std::cout << a.toString() << #operator << b.toString() << " => " << top().toString() << std::endl;)	\
		break;	\
		}

			case OP_LT: BINARY(<, push(False_);)
			case OP_LTE: BINARY(<=, push(False_);)
			case OP_GT: BINARY(>, push(False_);)
			case OP_GTE: BINARY(>=, push(False_);)

			case OP_SUB: BINARY(-, {})
			case OP_MUL: BINARY(*, {})
			case OP_DIV: BINARY(/, {})

			case OP_ADD: {
				Variable a = pop();
				Variable b = pop();
				if (a.type == Int_ && b.type == Int_) push(a.content.asInt + b.content.asInt);
				else if ((a.type == Float_ || a.type == Int_) && (b.type == Float_ || b.type == Int_)) {
					Float val_a = a.type == Float_ ? a.content.asFloat : (Float)a.content.asInt;
					Float val_b = b.type == Float_ ? b.content.asFloat : (Float)b.content.asInt;
					push(val_a + val_b);
				}
				else {
					// might be better to check type for error
					push(a.toString() + b.toString());
				}
				DEBUG(std::cout << a.toString() << " ADD " << b.toString() << " => " << top().toString() << std::endl;)
					break;
			}
			
			case OP_NEG: {
				Variable var = pop();
				if (var.type == Int_) push(-var.content.asInt);
				else if (var.type == Float_) push(-var.content.asFloat);
				else if (var.type == True_) push(False_);
				else if (var.type == False_) push(True_);
				DEBUG(std::cout << "NEG " << var.toString() << " => " << top().toString() << std::endl;)
				break;
			}
			

			case OP_PRINT: {
				std::cout << top().toString();
				DEBUG(std::cout << " asInt " << top().content.asInt << std::endl;)
				break;
			}

			case OP_PRINT_CHAR: {
				uchar* temp = (uchar*) &top().content.asInt;
				DEBUG(std::cout << "print " << +temp[0] << " " << +temp[1] << " " << +temp[2] << " " << +temp[3] << std::endl;)
				break;
			}
			
			case OP_SHOW_STACK: {
				std::cout << "\n<stack> \n";
				std::stack<Variable> temp = std::stack<Variable>(stack);
				while (!temp.empty()) {
					std::cout << "# " << temp.top().toString() << std::endl;
					temp.pop();
				}
				break;
			}

			default: {
				std::cout << "unknown operation : " << +opcode << std::endl;
			}
			
			} // end of switch
		}	// end of while
	}	// end of execute

};


int main(int argc, char* argv[]) {
	Interpreter o;
	if(argc==1){
		o.executeFromFile("../tests/test.hex");
	}
	else if(argc == 2){
		o.executeFromFile(argv[1]);
	}
	DEBUG(
		uchar c = OP_SHOW_STACK;
		o.execute(&c, 1);
	)
	return 0;
}