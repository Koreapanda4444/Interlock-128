set(INTERLOCK_RESEARCH_COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/research/run.py
    --source ${CMAKE_CURRENT_SOURCE_DIR} --driver $<TARGET_FILE:prefix_runner>
    --build-dir ${CMAKE_CURRENT_BINARY_DIR} --openssl-version=${OPENSSL_VERSION}
    --compiler-id ${CMAKE_C_COMPILER_ID} --compiler-version ${CMAKE_C_COMPILER_VERSION}
    --config=$<CONFIG>)
add_custom_target(research-smoke COMMAND ${INTERLOCK_RESEARCH_COMMAND} --profile smoke
    --output ${CMAKE_CURRENT_BINARY_DIR}/research/smoke.json DEPENDS prefix_runner VERBATIM)
add_custom_target(research-full COMMAND ${INTERLOCK_RESEARCH_COMMAND} --profile full
    --output ${CMAKE_CURRENT_BINARY_DIR}/research/full.json DEPENDS prefix_runner VERBATIM)
if(BUILD_TESTING)
  add_test(NAME research_harness COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_harness.py --driver $<TARGET_FILE:prefix_runner>)
  add_test(NAME research_smoke COMMAND ${INTERLOCK_RESEARCH_COMMAND} --profile smoke
      --output ${CMAKE_CURRENT_BINARY_DIR}/research/ctest-smoke.json)
  set_tests_properties(research_harness PROPERTIES TIMEOUT 30)
  set_tests_properties(research_smoke PROPERTIES TIMEOUT 120)
  add_test(NAME research_screening COMMAND ${Python3_EXECUTABLE}
      ${CMAKE_CURRENT_SOURCE_DIR}/research/test_screening.py)
endif()
