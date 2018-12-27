#pragma once
#include <iostream>
#include <cstdint>
#include <string>


typedef bool Bool;
typedef unsigned char uchar;
typedef std::int16_t Short;
typedef std::int32_t Int;
typedef float Float;
typedef std::string String;



//#define DEBUG_OPTION

#ifdef DEBUG_OPTION
#define DEBUG( content ) content
#else
#define DEBUG( content )
#endif