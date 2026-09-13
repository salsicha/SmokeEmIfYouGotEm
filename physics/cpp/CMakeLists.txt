cmake_minimum_required(VERSION 3.22)

project(raftsim_water VERSION 0.1.0 LANGUAGES CXX)
include(CTest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)
find_package(Chrono QUIET)

add_library(raftsim_water
  src/cartesian_domain.cpp
  src/chrono_bridge_fixtures.cpp
  src/chrono_coupling.cpp
  src/json.cpp
  src/numpy_io.cpp
  src/scenario.cpp
  src/solver_constriction_01.cpp
  src/solver_constriction_02.cpp
  src/solver_constriction_03.cpp
  src/solver_constriction_04.cpp
  src/solver_constriction_05.cpp
  src/solver_constriction_06.cpp
  src/solver_constriction_07.cpp
  src/solver_constriction_08.cpp
  src/solver_constriction_09.cpp
  src/solver_constriction_10.cpp
  src/solver_constriction_11.cpp
  src/solver_diagnostics.cpp
  src/solver_numerics.cpp
  src/solver_output.cpp
  src/solver_runtime.cpp
)
target_include_directories(raftsim_water PUBLIC include)
option(RAFTSIM_PROFILE_SOLVER "Emit opt-in native solver stage timings at thread exit" OFF)
if(RAFTSIM_PROFILE_SOLVER)
  target_compile_definitions(raftsim_water PRIVATE RAFTSIM_PROFILE_SOLVER=1)
endif()
target_link_libraries(raftsim_water PUBLIC ZLIB::ZLIB Threads::Threads)
target_compile_options(raftsim_water PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic>
)

add_executable(raftsim_water_solver tools/raftsim_water_solver.cpp)
target_link_libraries(raftsim_water_solver PRIVATE raftsim_water)

add_executable(raftsim_cartesian_cook tools/raftsim_cartesian_cook.cpp)
target_link_libraries(raftsim_cartesian_cook PRIVATE raftsim_water)

add_executable(raftsim_water_tests tests/raftsim_water_tests.cpp)
target_link_libraries(raftsim_water_tests PRIVATE raftsim_water)

add_executable(raftsim_cartesian_domain_tests tests/cartesian_domain_tests.cpp)
target_link_libraries(raftsim_cartesian_domain_tests PRIVATE raftsim_water)

if(BUILD_TESTING)
  add_test(NAME water_cartesian_domain COMMAND raftsim_cartesian_domain_tests)
  set_tests_properties(water_cartesian_domain PROPERTIES TIMEOUT 120)
  foreach(fixture wet_dry_shoreline lake_at_rest_balance transcritical_bump)
    add_test(NAME water_${fixture}
      COMMAND raftsim_water_tests
      "${CMAKE_CURRENT_SOURCE_DIR}/../data/validation/milestone17/analytic_fixtures/fixtures/${fixture}/scenario")
    set_tests_properties(water_${fixture} PROPERTIES TIMEOUT 120)
  endforeach()
endif()

add_executable(raftsim_chrono_bridge_fixtures tools/chrono_bridge_fixture_catalog.cpp)
target_link_libraries(raftsim_chrono_bridge_fixtures PRIVATE raftsim_water)

add_executable(raftsim_jolt_smoke_harness tools/jolt_smoke_harness.cpp)
target_link_libraries(raftsim_jolt_smoke_harness PRIVATE raftsim_water)

if(Chrono_FOUND)
  add_executable(raftsim_chrono_smoke tools/chrono_smoke_test.cpp)
  if(TARGET Chrono::Chrono)
    target_link_libraries(raftsim_chrono_smoke PRIVATE Chrono::Chrono)
  else()
    target_include_directories(raftsim_chrono_smoke PRIVATE ${CHRONO_INCLUDE_DIRS})
    target_link_libraries(raftsim_chrono_smoke PRIVATE ${CHRONO_LIBRARIES})
    if(CHRONO_CXX_FLAGS)
      separate_arguments(RAFTSIM_CHRONO_CXX_FLAGS NATIVE_COMMAND "${CHRONO_CXX_FLAGS}")
      target_compile_options(raftsim_chrono_smoke PRIVATE ${RAFTSIM_CHRONO_CXX_FLAGS})
    endif()
  endif()
else()
  message(STATUS "Project Chrono not found; skipping raftsim_chrono_smoke target")
endif()
