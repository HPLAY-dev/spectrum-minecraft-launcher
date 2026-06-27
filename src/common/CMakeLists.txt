add_library(mc_common STATIC
    src/utils.cpp
    src/paths.cpp
)

target_include_directories(mc_common
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(mc_common PUBLIC cxx_std_17)
