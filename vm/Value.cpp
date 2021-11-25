#include "common.h"


enum Type {
	None,

	False,
	True,

	IntType,
	FloatType,
	StringType,
};

const String Type_string[] = {
	"None",
	"False",
	"True",
	"Int",
	"Float",
	"String",
};



union Value {
public:
	Int asInt = 0;
	Float asFloat;
	String* asString;

	Value() {}
	~Value() {}
};




class Variable {
public:

	Type type = None;
	Value content;

	Variable() {}
	Variable(Type t){ 	type = t; }
	Variable(Bool t){ 	type = t ? True : False; }
	Variable(Int i){ 	content.asInt = i; type = IntType; }
	Variable(Float f){ 	content.asFloat = f; type = FloatType; }
	Variable(String s){ content.asString = new String(s); type = StringType; }
	Variable(String* s){content.asString = s; type = StringType; }
	Variable(const Variable& v) { copy(v, *this); }


	~Variable() {
		//DEBUG(std::cout << "DEATH of a " << Type_string[type] << " : "<< toString() << "\n";)
		if (type == StringType && content.asString!=nullptr) delete content.asString;
	}


	String toString() const {
		switch (type) {
		case None:
			return "None";
		case False:
			return "False";
		case True:
			return "True";
		case IntType:
			return std::to_string(content.asInt);
		case FloatType:
			return std::to_string(content.asFloat );
		case StringType:
			return *content.asString;
		default:
			return "<no representation>";
		}
	}

	static void copy(const Variable& from, Variable& to) {
		to.type = from.type;
		if (from.type == StringType){
			to.content.asString = new String(*from.content.asString);
		}
		else to.content = from.content;
	}
};

