#define _SCL_SECURE_NO_WARNINGS
#include <stack>
#include <vector>
#include <fstream>
#include "opcodes.h"
#include "Value.cpp"

////////////////////////////////////
/// the instruction container
////////////////////////////////////
class ByteCode {
public:

	Int size = 0;
	uchar* bytes;
	Int pointer = 0;
	ByteCode(){}
	ByteCode(uchar* data, Int length) : bytes(data), size(length) {
		DEBUG(
			std::cout<< "size " << size << "\n";
			for(int i=0; i<size; i++)
					std::cout<< (+data[i]) << " ";
				std::cout<<"\n";
		)
	}

	uchar next() {
		uchar ret;
		if(pointer<size){
			ret = bytes[pointer];
			DEBUG(
				if (ret>OP_END){
					std::cout << "Error " << pointer << " : " << +ret << " is not known opcode\n";
					return OP_END;
				}
			)
		}
		else
			ret = OP_END;
		DEBUG(std::cout << pointer << "\t: " << +ret << "\t";)
		pointer++;
		return ret;
	}
	template<typename T> T read() {
		T result = *(T*)(bytes + pointer);
		pointer += sizeof(T);
		return result;
	}
	uchar current() { return bytes[pointer-1]; }
	uchar peek() { return bytes[pointer]; }
	inline void reset() { pointer = 0; }
};


////////////////////////////////////
/// the virtual machine
////////////////////////////////////
class Interpreter {
public:
	std::stack<Variable> stack;
	std::vector<Variable> registers;
	Interpreter() : registers(256) {}
	ByteCode code;

	inline Variable& top() { return stack.top(); }
	inline Variable pop() { Variable var(top()); stack.pop(); return var; }
	template<typename T> inline void push(T arg) { stack.emplace<Variable>(arg); }
	

	void execute_switch();

	void execute(ByteCode b) {
		code = b;
		execute_switch();
	}
	void execute(String fileName) {
		std::ifstream in(fileName, std::ios::binary);
		std::vector<uchar> buffer((
			std::istreambuf_iterator<char>(in)),
			(std::istreambuf_iterator<char>()));
		buffer.shrink_to_fit();
		ByteCode b = ByteCode(buffer.data(), buffer.size());
		execute(b);
	}

////////////////////////////////////
/// the operations
////////////////////////////////////

	inline void no_op() { 
			DEBUG(std::cout << "NOOP " << std::endl;)
		}

	inline void op_none(){
		push( None_ );
		DEBUG(std::cout << "none " << std::endl;)
	}

	inline void op_true(){
		push( True_ );
		DEBUG(std::cout << "true " << std::endl;)
	}

	inline void op_false(){
		push( False_ );
		DEBUG(std::cout << "false " << std::endl;)
	}

	inline void op_int1(){
		push((Int)code.read<char>());
		DEBUG(std::cout << "int1 " << top().toString() << std::endl;)
	}
	inline void op_int2(){
		push((Int)code.read<Short>());
		DEBUG(std::cout << "int2 " << top().toString() << std::endl;)
	}
	inline void op_int4(){
		push(code.read<Int>());
		DEBUG(std::cout << "int4 " << top().toString() << std::endl;)
	}
	
	inline void op_float(){
		push(code.read<Float>());
		DEBUG(std::cout << "float " << top().toString() << std::endl;)
	}
	
	inline void op_string(){
		String* s = new String();
		DEBUG(std::cout << "string ";)
		for (char c = code.read<uchar>(); c != 0; c = code.read<uchar>()) {
			*s += c;
			DEBUG(std::cout << c << std::flush;)
		}
		DEBUG(std::cout << std::endl;)
		push( s );
	}

	
	inline void op_load(){
		uchar address = code.read<uchar>();
		Variable var = registers[address];
		// compiler says no copy construction #WorkAroundFTW
		push(None_);
		Variable::copy(var, top());
		DEBUG(std::cout << "LOAD " << +address << " : " << var.toString() << std::endl;)
	}

	inline void op_store(){
		uchar address = code.read<uchar>();
		Variable var = pop();
		registers[address] = var;
		DEBUG(std::cout << "STORE " << +address << " : " << var.toString() << std::endl;)
	}

	inline void op_pop(){
		pop();
		DEBUG(std::cout << "POP" << std::endl;)
	}
	

	inline void op_jump(){
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump => " << code.pointer+distance << std::endl;)
		code.pointer += distance;
	}
	inline void op_jump_if(){
		Variable condition = top();
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump if true => " << code.pointer+distance << std::endl;)
		if (condition.type == True_) {
			code.pointer += distance;
		}
	}
	inline void op_jump_if_false(){
		Variable condition = top();
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump if false => " << code.pointer+distance << std::endl;)
		if (condition.type != True_) {
			code.pointer += distance;
		}
	}
#define BINARY_IMPL(operator) \
Variable b = pop();					\
Variable a = pop();					\
if (a.type == Int_ && b.type == Int_) 						\
	push(a.content.asInt operator b.content.asInt); 		\
else if(a.type == Float_ && b.type == Int_)					\
	push(a.content.asFloat operator (Float)b.content.asInt);\
else if(a.type == Int_ && b.type == Float_)					\
	push((Float)a.content.asInt operator b.content.asFloat);\

#define BINARY(operator, other) {	\
BINARY_IMPL(operator)				\
else other							\
DEBUG(std::cout << a.toString() << #operator << b.toString() << " => " << top().toString() << std::endl;) \
}

#define BINARY_EXTENDED(operator) 				\
BINARY(operator, 								\
if (a.type == String_ && b.type == String_) 	\
	push(a.toString() operator b.toString());	\
else push(a.type operator b.type);				\
)
	
	inline void op_eq() BINARY_EXTENDED(==)
	inline void op_neq() BINARY_EXTENDED(!=)

	inline void op_lt()  BINARY_EXTENDED(<)
	inline void op_lte() BINARY_EXTENDED(<=)
	inline void op_gt()  BINARY_EXTENDED(>)
	inline void op_gte() BINARY_EXTENDED(>=)

	inline void op_sub() BINARY(-, {})
	inline void op_mul() BINARY(*, {})
	inline void op_div() BINARY(/, {})

	inline void op_add() BINARY_EXTENDED(+)
	
	inline void op_neg(){
		Variable var = pop();
		if (var.type == Int_) push(-var.content.asInt);
		else if (var.type == Float_) push(-var.content.asFloat);
		else if (var.type == True_) push(False_);
		else if (var.type == False_) push(True_);
		DEBUG(std::cout << "NEG " << var.toString() << " => " << top().toString() << std::endl;)
	}
	

	inline void op_print(){
		std::cout << top().toString();
		DEBUG(std::cout << " asInt " << top().content.asInt << std::endl;)
	}
	
	inline void op_show_stack(){
		std::cout << "\n<stack> \n";
		std::stack<Variable> temp = std::stack<Variable>(stack);
		while (!temp.empty()) {
			std::cout << "# " << temp.top().toString() << std::endl;
			temp.pop();
		}
	}

	inline void op_show_registers(){
		std::cout << "\n<registers> \n";
		for(auto var : registers) {
			std::cout << " #" << var.toString();
		}
	}

	inline void op_end(){
		DEBUG(std::cout << "END" << std::endl;)
	}
};


int main(int argc, char* argv[]) {
	Interpreter i;
	if(argc==1){
		i.execute("../tests/test.hex");
	}
	else if(argc == 2){
		i.execute(argv[1]);
	}
	DEBUG(
		i.op_show_stack();
		i.op_show_registers();
	)
	return 0;
}
