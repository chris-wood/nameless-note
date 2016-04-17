cmake_minimum_required(VERSION 2.8)

project (hashing_overhead)
set(CMAKE_BUILD_TYPE Release)

#set(GCC_COVERAGE_COMPILE_FLAGS "-ftest-coverage -fprofile-arcs -pg")
#set(GCC_COVERAGE_LINK_FLAGS    "-pg")
#set( CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} ${GCC_COVERAGE_COMPILE_FLAGS}" )
#set( CMAKE_EXE_LINKER_FLAGS  "${CMAKE_EXE_LINKER_FLAGS} ${GCC_COVERAGE_LINK_FLAGS}" )

include_directories(
        /Users/cwood/PARC/side/Improvements/src/Libparc
        /Users/cwood/PARC/side/Improvements/src/Libccnx-common
        /Users/cwood/PARC/side/Improvements/usr/include/
    )

set(SOURCES hashing_overhead.c)

link_directories(
        /Users/cwood/PARC/side/Improvements/usr/lib
    )

add_executable(hashing_overhead ${SOURCES})
set_target_properties(hashing_overhead PROPERTIES COMPILE_FLAGS "-Wall -pg")

target_link_libraries(hashing_overhead longbow longbow-ansiterm parc ccnx_common ccnx_api_portal ccnx_api_notify ccnx_api_control ccnx_transport_rta)

install(TARGETS hashing_overhead DESTINATION bin)
