add_executable(test_utils test_utils.cpp)
target_link_libraries(test_utils PRIVATE mc_common)
add_test(NAME utils COMMAND test_utils)
