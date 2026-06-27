import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

ApplicationWindow {
    id: window
    width: 1024
    height: 680
    visible: true
    title: "MC Launcher"

    color: SpectrumTheme.background

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        Text {
            text: "MC Launcher"
            font.pixelSize: 28
            font.bold: true
            color: SpectrumTheme.textTitle
        }

        Text {
            text: "PySide6 + Qt6 QML — Rust 核心 / C++ 引擎 / Python 桥接"
            color: SpectrumTheme.textMuted
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        SpectrumCard {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                Text {
                    text: "版本列表（前 50 条）"
                    color: SpectrumTheme.textMuted
                }

                ListView {
                    id: versionList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: JSON.parse(App.getVersionList())
                    delegate: Rectangle {
                        width: versionList.width
                        height: 32
                        radius: 4
                        color: index % 2 === 0 ? SpectrumTheme.surfaceHover : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            text: modelData
                            color: SpectrumTheme.text
                        }
                    }
                }

                PrimaryButton {
                    text: "刷新版本"
                    onClicked: {
                        App.refreshVersionList()
                        versionList.model = JSON.parse(App.getVersionList())
                    }
                }
            }
        }
    }

    Component.onCompleted: App.refreshVersionList()
}
