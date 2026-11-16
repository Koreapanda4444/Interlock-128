add_executable(interlock_bench bench/native.c bench/interlock_backend.c)
target_include_directories(interlock_bench PRIVATE bench)
target_link_libraries(interlock_bench PRIVATE interlock OpenSSL::Crypto)
if(MSVC)
  target_compile_options(interlock_bench PRIVATE /W4)
else()
  target_compile_options(interlock_bench PRIVATE -Wall -Wextra -Wpedantic -Wconversion)
endif()
set(INTERLOCK_BENCH_COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/bench/run.py
    --source ${CMAKE_CURRENT_SOURCE_DIR} --driver $<TARGET_FILE:interlock_bench>
    --build-dir ${CMAKE_CURRENT_BINARY_DIR} --compiler-id ${CMAKE_C_COMPILER_ID}
    --compiler-version ${CMAKE_C_COMPILER_VERSION} --config=$<CONFIG>)
add_custom_target(bench COMMAND ${INTERLOCK_BENCH_COMMAND}
    --output ${CMAKE_CURRENT_BINARY_DIR}/bench/full.json DEPENDS interlock_bench VERBATIM)
if(BUILD_TESTING)
  add_test(NAME benchmark_smoke COMMAND ${INTERLOCK_BENCH_COMMAND} --target-ms 1
      --output ${CMAKE_CURRENT_BINARY_DIR}/bench/smoke.json)
  set_tests_properties(benchmark_smoke PROPERTIES TIMEOUT 240)
endif()
