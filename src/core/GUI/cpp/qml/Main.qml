import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 960
    height: 640
    visible: true
    title: "SerenaLauncher (Qt6 C++)"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Label {
            text: "SerenaLauncher"
            font.pixelSize: 28
            font.bold: true
        }

        Label {
            text: "26Q2 · 开发代号 Okra · 大版本 26"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Label {
            text: "Qt6 C++ GUI 入口 — 与 Python / Rust GUI 共享 C++ 核心库"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Button {
            text: "占位：启动游戏"
            Layout.alignment: Qt.AlignLeft
        }

        Item { Layout.fillHeight: true }
    }
}
