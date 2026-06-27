cmake_minimum_required(VERSION 3.20)
project(serena_launcher VERSION 26.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MC_BUILD_CPP_GUI "Build Qt6 C++ GUI target" ON)
option(MC_BUILD_TESTS "Build C++ unit tests" OFF)

add_subdirectory(src/common)
add_subdirectory(src/core)
add_subdirectory(src/launcher)

if(MC_BUILD_CPP_GUI)
    add_subdirectory(src/core/GUI/cpp)
endif()

if(MC_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests/cpp)
endif()
