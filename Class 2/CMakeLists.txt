cmake_minimum_required(VERSION 3.21)

if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
    set(CMAKE_INSTALL_PREFIX "${CMAKE_SOURCE_DIR}/install" CACHE PATH "Install path prefix" FORCE)
endif()

project(Class2App VERSION 1.0 LANGUAGES CXX)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
find_package(Qt6 QUIET COMPONENTS WebEngineWidgets)

set(SOURCES
    src/main.cpp
    src/mainwindow.cpp
    src/mainwindow.ui
    src/latexwidget.cpp
    src/functioncatalog.cpp
    src/functionselector.cpp
    src/graphwidget.cpp
)

add_executable(Class2App ${SOURCES})

target_link_libraries(Class2App PRIVATE Qt6::Core Qt6::Gui Qt6::Widgets)
if(TARGET Qt6::WebEngineWidgets)
    target_link_libraries(Class2App PRIVATE Qt6::WebEngineWidgets)
    target_compile_definitions(Class2App PRIVATE CLASS2_HAS_WEBENGINE=1)
endif()
target_compile_options(Class2App PRIVATE "$<$<CONFIG:Release>:-O3;-DNDEBUG>")
target_link_options(Class2App PRIVATE -static-libgcc -static-libstdc++ -static)

get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
get_filename_component(QT_BIN_DIR "${QT_QMAKE_EXECUTABLE}" DIRECTORY)
find_program(WINDEPLOYQT_EXECUTABLE windeployqt HINTS "${QT_BIN_DIR}")

if(WINDEPLOYQT_EXECUTABLE)
    add_custom_target(deploy_qt
        COMMAND "${WINDEPLOYQT_EXECUTABLE}" --dir "$<TARGET_FILE_DIR:Class2App>" "$<TARGET_FILE:Class2App>"
        DEPENDS Class2App
        COMMENT "Deploying Qt runtime dependencies"
    )
endif()

install(TARGETS Class2App DESTINATION bin)
