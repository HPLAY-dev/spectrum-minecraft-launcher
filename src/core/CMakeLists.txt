add_library(mc_core STATIC
    src/engine.cpp
    src/instance_manager.cpp
)

target_include_directories(mc_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(mc_core PUBLIC mc_common)
target_compile_features(mc_core PUBLIC cxx_std_17)
