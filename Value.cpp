#include "common.h"


enum Type {
	None_,

	False_,
	True_,

//	Error_,
//	Done_,

	Int_,
	Float_,
	String_,
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

	Type type = None_;
	Value content;

	Variable() {}
	Variable(Type t){ 	type = t; }
	Variable(Bool t){ 	type = t ? True_ : False_; }
	Variable(Int i){ 	content.asInt = i; type = Int_; }
	Variable(Float f){ 	content.asFloat = f; type = Float_; }
	Variable(String s){ content.asString = new String(s); type = String_; }
	Variable(String* s){content.asString = s; type = String_; }
	Variable(const Variable& v) { copy(v, *this); }


	~Variable() {
		//DEBUG(std::cout << "DEATH of a " << Type_string[type] << " : "<< toString() << "\n";)
		if (type == String_ && content.asString!=nullptr) delete content.asString;
	}


	String toString() const {
		switch (type) {
		case None_:
			return "None";
		case False_:
			return "False";
		case True_:
			return "True";
//		case Error_:
//			return *value.asString;
//		case Done_:
//			return "Done";
		case Int_:
			return std::to_string(content.asInt);
		case Float_:
			return std::to_string(content.asFloat );
		case String_:
			return *content.asString;
		default:
			return "<no representation>";
		}
	}

	static void copy(const Variable& from, Variable& to) {
		to.type = from.type;
		if (from.type == String_){
			to.content.asString = new String(*from.content.asString);
		}
		else to.content = from.content;
	}
};

