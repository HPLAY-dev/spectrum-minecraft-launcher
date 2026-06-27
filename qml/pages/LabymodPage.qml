import QtQuick
import QtQuick.Controls
import Spectrum

SpectrumCard {
    anchors.fill: parent

    Column {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "LabyMod"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        Row {
            spacing: 16
            width: parent.width

            ListView {
                id: lmList
                width: parent.width * 0.45
                height: 280
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

            Column {
                spacing: 10
                width: parent.width * 0.45

                Text { text: "实例名称"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                TextField {
                    width: parent.width
                    placeholderText: "labymod-instance"
                    onTextChanged: App.setLabymodInstanceName(text)
                }

                PrimaryButton {
                    text: "下载 LabyMod"
                    width: parent.width
                    onClicked: App.downloadLabymod()
                }
            }
        }
    }
}
