cmake_minimum_required(VERSION 3.22)

project(raftsim_water VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(ZLIB REQUIRED)

add_library(raftsim_water
  src/json.cpp
  src/numpy_io.cpp
  src/scenario.cpp
  src/solver.cpp
)
target_include_directories(raftsim_water PUBLIC include)
target_link_libraries(raftsim_water PUBLIC ZLIB::ZLIB)
target_compile_options(raftsim_water PRIVATE
  $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall -Wextra -Wpedantic>
)

add_executable(raftsim_water_solver tools/raftsim_water_solver.cpp)
target_link_libraries(raftsim_water_solver PRIVATE raftsim_water)

add_executable(raftsim_water_tests tests/raftsim_water_tests.cpp)
target_link_libraries(raftsim_water_tests PRIVATE raftsim_water)

