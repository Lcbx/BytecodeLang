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
	Byte* bytes;
	Int pointer = 0;
	ByteCode(){}
	ByteCode(Byte* data, Int length) : bytes(data), size(length) {
		DEBUG(
			std::cout<< "size " << size << "\n";
			for(int i=0; i<size; i++)
					std::cout<< (+data[i]) << " ";
				std::cout<<"\n";
		)
	}

	Byte next() {
		Byte ret;
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
	Byte current() { return bytes[pointer-1]; }
	Byte peek() { return bytes[pointer]; }
	inline void reset() { pointer = 0; }
};


////////////////////////////////////
/// the virtual machine
////////////////////////////////////
class Interpreter {
public:
	std::deque<Variable> stack;
	Interpreter() {}
	ByteCode code;

	inline Variable& top() { return stack.back(); }
	inline Variable pop() { Variable var(top()); stack.pop_back(); return var; }
	template<typename T> inline void push(T arg) { stack.emplace_back<Variable>(arg); }
	

	void execute_switch();

	void execute(ByteCode b) {
		code = b;
		execute_switch();
	}
	void execute(String fileName) {
		std::ifstream in(fileName, std::ios::binary);
		std::vector<Byte> buffer((
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
		push( None );
		DEBUG(std::cout << "none " << std::endl;)
	}

	inline void op_true(){
		push( True );
		DEBUG(std::cout << "true " << std::endl;)
	}

	inline void op_false(){
		push( False );
		DEBUG(std::cout << "false " << std::endl;)
	}

	inline void op_int1(){
		push((Int)code.read<Byte>());
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
		for (Byte c = code.read<Byte>(); c != 0; c = code.read<Byte>()) {
			*s += c;
			DEBUG(std::cout << c << std::flush;)
		}
		DEBUG(std::cout << std::endl;)
		push( s );
	}

	
	inline void op_load(){
		Byte address = code.read<Byte>();
		Variable var = stack[address];
		// compiler says no copy construction #WorkAroundFTW
		push(None);
		Variable::copy(var, top());
		DEBUG(std::cout << "LOAD " << +address << " : " << var.toString() << std::endl;)
	}

	inline void op_store(){
		Byte address = code.read<Byte>();
		if (address!=stack.size()-1){
			Variable var = pop();
			stack[address] = var;
			DEBUG(std::cout << "STORE " << +address << " : " << var.toString() << std::endl;)
		}
		DEBUG(else std::cout << "STORE " << +address << std::endl;)
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
		if (condition.type == True) {
			code.pointer += distance;
		}
	}
	inline void op_jump_if_false(){
		Variable condition = top();
		Short distance = code.read<Short>();
		DEBUG(std::cout << "jump if false => " << code.pointer+distance << std::endl;)
		if (condition.type != True) {
			code.pointer += distance;
		}
	}

#define BINARY_IMPL(operator, other) 								\
Variable b = pop();													\
Variable a = pop();													\
if (a.type == IntType && b.type == IntType) 						\
	push(a.content.asInt operator b.content.asInt); 				\
else if(a.type == FloatType && b.type == FloatType)					\
	push(a.content.asFloat operator b.content.asFloat); 			\
else if(a.type == FloatType && b.type == IntType)					\
	push(a.content.asFloat operator (Float)b.content.asInt);		\
else if(a.type == IntType && b.type == FloatType)					\
	push((Float)a.content.asInt operator b.content.asFloat);		\
other																\
DEBUG(std::cout << a.toString() << #operator << b.toString() << " => " << top().toString() << std::endl;) \

#define BINARY(operator) {	\
BINARY_IMPL(operator, )	\
}

#define BINARY_EXTENDED(operator) 						\
BINARY(operator, 										\
else if (a.type == StringType && b.type == StringType) 	\
	push(a.toString() operator b.toString());			\
else push(a.type operator b.type);						\
)
	
	inline void op_eq()  BINARY_EXTENDED(==)
	inline void op_neq() BINARY_EXTENDED(!=)

	inline void op_lt()  BINARY_EXTENDED(<)
	inline void op_lte() BINARY_EXTENDED(<=)
	inline void op_gt()  BINARY_EXTENDED(>)
	inline void op_gte() BINARY_EXTENDED(>=)

	inline void op_sub() BINARY(-)
	inline void op_mul() BINARY(*)
	inline void op_div() BINARY(/)

	inline void op_add() BINARY_EXTENDED(+)
	
	inline void op_neg(){
		Variable var = pop();
		if (var.type == IntType)		push(-var.content.asInt);
		else if (var.type == FloatType) push(-var.content.asFloat);
		else if (var.type == True)		push(False);
		else if (var.type == False)		push(True);
		DEBUG(std::cout << "NEG " << var.toString() << " => " << top().toString() << std::endl;)
	}
	

	inline void op_print(){
		DEBUG(std::cout << "print ";)
		std::cout << top().toString();
		DEBUG(std::cout << " asInt " << top().content.asInt << std::endl;)
	}
	
	inline void op_show_stack(){
		std::cout << "\n<stack> \n";
		for( auto it : stack) {
			std::cout << "# " << it.toString() << std::endl;
		}
	}

	inline void op_end(){
		DEBUG(std::cout << "END" << std::endl;)
	}
};


int main(int argc, char* argv[]) {
	Interpreter i;
	try{
		if(argc==1){
			i.execute("../tests/test.hex");
		}
		else if(argc == 2){
			i.execute(argv[1]);
		}
	}
	catch(std::exception ex) {
		DEBUG(std::cerr << "ex"  << ex.what() << std::endl;)
	}
	DEBUG(
		i.op_show_stack();
	)
	return 0;
}
