cmake_minimum_required(VERSION 3.8)

# Compiler and Standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)

# set the project name
set(PROJECT VM)

# RUST, Erlang, what else
project(${PROJECT} C CXX)

# add sources
file(GLOB SOURCES
    *.c
    *.cpp
)
file(GLOB HEADERS
	*.h
	*.hpp
)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ..)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ..)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ..)

# add the executable
add_executable(${PROJECT} ${SOURCES} ${HEADERS})


