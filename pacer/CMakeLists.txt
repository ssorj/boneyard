cmake_minimum_required (VERSION 2.6)
project (Pacer)
include_directories(include)

file(GLOB_RECURSE _main_files "${CMAKE_SOURCE_DIR}/src/*.cpp" "${CMAKE_SOURCE_DIR}/src/*.h")

add_executable(main ${_main_files})

get_cmake_property(_var_names VARIABLES)
foreach (_var_name ${_var_names})
    message(STATUS "${_var_name}=${${_var_name}}")
endforeach()

## Things I learned
#
# - CMAKE_SOURCE_DIR is the project dir, not the source code subtree
# - GLOB_RECURSE has some pretty bad behavior with relative paths;
#   see http://public.kitware.com/Bug/view.php?id=11043
#   (and they shouldn't have closed that bug IMO)
