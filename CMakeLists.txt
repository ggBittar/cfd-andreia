cmake_minimum_required(VERSION 3.21)

project(avaliador_derivadas
    VERSION 1.0.0
    DESCRIPTION "Aplicacao Qt para comparar aproximacoes numericas de derivadas"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Widgets)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Widgets)

add_executable(avaliador_derivadas
    src/main.cpp
    src/aproximacoes.cpp
    src/aproximacoes.hpp
    src/grafico_funcao.cpp
    src/grafico_funcao.hpp
    src/janela_principal.cpp
    src/janela_principal.hpp
    recursos/tema.qrc
)

target_link_libraries(avaliador_derivadas PRIVATE Qt${QT_VERSION_MAJOR}::Widgets)

if(WIN32)
    set_target_properties(avaliador_derivadas PROPERTIES WIN32_EXECUTABLE TRUE)
    set_target_properties(avaliador_derivadas PROPERTIES
        VS_DEBUGGER_WORKING_DIRECTORY "$<TARGET_FILE_DIR:avaliador_derivadas>"
    )

    find_program(WINDEPLOYQT_EXECUTABLE windeployqt HINTS "${CMAKE_PREFIX_PATH}/bin")
    if(WINDEPLOYQT_EXECUTABLE)
        add_custom_command(TARGET avaliador_derivadas POST_BUILD
            COMMAND "${WINDEPLOYQT_EXECUTABLE}"
                --release
                --no-compiler-runtime
                "$<TARGET_FILE:avaliador_derivadas>"
            COMMENT "Deploying Qt runtime dependencies"
        )
    endif()
endif()
