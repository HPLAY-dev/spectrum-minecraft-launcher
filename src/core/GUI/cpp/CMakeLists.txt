find_package(Qt6 REQUIRED COMPONENTS Core Gui Qml Quick QuickControls2)

qt_standard_project_setup()

qt_add_executable(mc_launcher_qt
    main.cpp
)

qt_add_qml_module(mc_launcher_qt
    URI McLauncher
    VERSION 1.0
    QML_FILES
        qml/Main.qml
)

target_link_libraries(mc_launcher_qt
    PRIVATE
        Qt6::Core
        Qt6::Gui
        Qt6::Qml
        Qt6::Quick
        Qt6::QuickControls2
        mc_core
        mc_common
)
