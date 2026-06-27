import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    id: root
    anchors.fill: parent

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "LabyMod"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            Item {
                Layout.preferredWidth: Math.round(root.width * 0.42)
                Layout.fillHeight: true

                ListView {
                    id: lmList
                    anchors.fill: parent
                    clip: true
                    model: App.getLabymodVersions()
                    delegate: Rectangle {
                        width: lmList.width
                        height: 36
                        color: lmList.currentIndex === index ? SpectrumTheme.primary : "transparent"
                        radius: 4
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: lmList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.text
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                lmList.currentIndex = index
                                App.selectLabymodVersion(index)
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                Text { text: "实例名称"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                TextField {
                    Layout.fillWidth: true
                    placeholderText: "labymod-instance"
                    onTextChanged: App.setLabymodInstanceName(text)
                }

                PrimaryButton {
                    text: "下载 LabyMod"
                    Layout.fillWidth: true
                    onClicked: App.downloadLabymod()
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    Connections {
        target: App
        function onLabymodVersionsChanged() {
            lmList.model = App.getLabymodVersions()
        }
    }
}
