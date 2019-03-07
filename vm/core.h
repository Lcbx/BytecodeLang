#define _SCL_SECURE_NO_WARNINGS
#include <stack>
#include <vector>
#include <fstream>
#include "opcodes.h"
#include "Value.cpp"


class ByteCode {
public:

	Int max = 0;
	uchar* bytes;
	Int pointer = 0;
	bool ended = false;
	ByteCode(){}
	ByteCode(uchar* s, Int length) : bytes(s), max(length) {
		DEBUG(
			for(int i=0; i<length; i++)
					std::cout<< ((int) s[i]) << " ";
				std::cout<<"\n";
		)
	}
	uchar next() {
		if(pointer<max)
			return bytes[pointer++];
		else {
			ended = true;
			return 0;
		}
	}
	template<typename T> T read() {
		T result = *(T*)(bytes + pointer);
		pointer += sizeof(T);
		return result;
	}
	uchar current() { return bytes[pointer-1]; }
	uchar peek() { return bytes[pointer]; }
	void reset() { pointer = 0; }
	void jump(Int i) { pointer += i; }
};



class Interpreter {
public:
	std::stack<Variable> stack;
	std::deque<Variable> registers;
	Interpreter() : registers(0) {} //max 256
	ByteCode code;

	inline Variable& top() { return stack.top(); }
	Variable pop() { Variable var(top()); stack.pop(); return var; }
	template<typename T> void push(T arg) { stack.emplace<Variable>(arg); }
	

	void execute_switch();

	void execute(uchar* s, Int length) {
		code = ByteCode(s, length);
		execute_switch();
	}

	void executeFromFile(String fileName) {
		std::ifstream in(fileName, std::ios::binary);
		std::vector<uchar> buffer((
			std::istreambuf_iterator<char>(in)),
			(std::istreambuf_iterator<char>()));
		buffer.shrink_to_fit();
		execute(buffer.data(), buffer.size());
	}

	void no_op() { 
			DEBUG(std::cout << "NOOP " << std::endl;)
		}

	void op_none(){
		push( None_ );
		DEBUG(std::cout << "none " << std::endl;)
	}

	void op_true(){
		push( True_ );
		DEBUG(std::cout << "true " << std::endl;)
	}

	void op_false(){
		push( False_ );
		DEBUG(std::cout << "false " << std::endl;)
	}

	void op_int(){
		push(code.read<Int>());
		DEBUG(std::cout << "int " << top().toString() << std::endl;)
	}
	
	void op_float(){
		push(code.read<Float>());
		DEBUG(std::cout << "float " << top().toString() << std::endl;)
	}
	
	void op_string(){
		String* s = new String();
		DEBUG(std::cout << "string ";)
		for (char c = code.next(); c != 0; c = code.next()) {
			*s += c;
			DEBUG(std::cout << c << std::flush;)
		}
		DEBUG(std::cout << std::endl;)
		push( s );
	}

	
	void op_load(){
		uchar address = code.read<uchar>();
		Variable var = registers[address];
		// compiler says no copy construction #WorkAroundFTW
		push(None_);
		Variable::copy(var, top());
		DEBUG(std::cout << "LOAD " << +address << " : " << var.toString() << std::endl;)
	}

	void op_store(){
		uchar address = code.read<uchar>();
		Variable var = pop();
		registers[address] = var;
		DEBUG(std::cout << "STORE " << +address << " : " << var.toString() << std::endl;)
	}

	void op_pop(){
		pop();
		DEBUG(std::cout << "POP" << std::endl;)
	}
	

	void op_jump(){
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump => " << code.pointer+distance << std::endl;)
		code.pointer += distance;
	}
	void op_jump_if(){
		Variable condition = top();
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump if true => " << code.pointer+distance << std::endl;)
		if (condition.type == True_) {
			code.pointer += distance;
		}
	}
	void op_jump_if_false(){
		Variable condition = top();
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump if false => " << code.pointer+distance << std::endl;)
		if (condition.type != True_) {
			code.pointer += distance;
		}
	}

	void op_eq(){
		Variable a = pop();
		Variable b = pop();
		if (a.type == Int_ && b.type == Int_)
			push(a.content.asInt == b.content.asInt);
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
	}
	
	void op_neq(){
		Variable a = pop();
		Variable b = pop();
		if (a.type == Int_ && b.type == Int_)
			push(a.content.asInt != b.content.asInt);
		else if ((a.type == Float_ || a.type == Int_) && (b.type == Float_ || b.type == Int_)) {
			Float val_a = a.type == Float_ ? a.content.asFloat : (Float)a.content.asInt;
			Float val_b = b.type == Float_ ? b.content.asFloat : (Float)b.content.asInt;
			push(val_a != val_b);
		}
		else if (a.type == String_ && b.type == String_) {
			push(a.toString() != b.toString());
		}
		////////////
		// INSERT COMP OF ARRAYS AND OBJ HERE
		////////////
		else if (a.type != b.type) push(True_); // None == None, False == False, etc
		else push(False_);
		DEBUG(std::cout << a.toString() << " != " << b.toString() << " => " << top().toString() << std::endl;)
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
}

	void op_lt()  BINARY(<, push(False_);)
	void op_lte() BINARY(<=, push(False_);)
	void op_gt()  BINARY(>, push(False_);)
	void op_gte() BINARY(>=, push(False_);)

	void op_sub() BINARY(-, {})
	void op_mul() BINARY(*, {})
	void op_div() BINARY(/, {})

	void op_add(){
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
	}
	
	void op_neg(){
		Variable var = pop();
		if (var.type == Int_) push(-var.content.asInt);
		else if (var.type == Float_) push(-var.content.asFloat);
		else if (var.type == True_) push(False_);
		else if (var.type == False_) push(True_);
		DEBUG(std::cout << "NEG " << var.toString() << " => " << top().toString() << std::endl;)
	}
	

	void op_print(){
		std::cout << top().toString();
		DEBUG(std::cout << " asInt " << top().content.asInt << std::endl;)
	}

	void op_print_char(){
		uchar* temp = (uchar*) &top().content.asInt;
		DEBUG(std::cout << "print " << +temp[0] << " " << +temp[1] << " " << +temp[2] << " " << +temp[3] << std::endl;)
	}
	
	void op_show_stack(){
		std::cout << "\n<stack> \n";
		std::stack<Variable> temp = std::stack<Variable>(stack);
		while (!temp.empty()) {
			std::cout << "# " << temp.top().toString() << std::endl;
			temp.pop();
		}
	}
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
