import QtQuick
import QtQuick.Controls
import Spectrum

SpectrumCard {
    anchors.fill: parent

    Flickable {
        anchors.fill: parent
        contentHeight: col.height
        clip: true

        Column {
            id: col
            width: parent.width
            spacing: 14

            Text {
                text: "设置"
                font.pixelSize: 22
                font.family: SpectrumTheme.fontCnTitle
                font.weight: SpectrumTheme.weightCnTitle
            }

            Text { text: "Minecraft 目录"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
            Row {
                spacing: 8
                width: parent.width
                TextField {
                    id: mcDir
                    width: parent.width - 120
                    text: App.getMinecraftDir()
                    onEditingFinished: App.setMinecraftDir(text)
                }
                PrimaryButton {
                    text: "浏览"
                    filled: false
                    onClicked: mcDir.text = App.browseMinecraftDir()
                }
            }

            Text { text: "Java 运行时"; color: SpectrumTheme.textMuted; font.pixelSize: 13; topPadding: 8 }
            ComboBox {
                id: javaCombo
                width: parent.width
                model: App.getJavaRuntimes()
                textRole: "label"
                onActivated: {
                    var item = javaCombo.model[currentIndex]
                    if (item && item.path)
                        App.selectJava(item.path)
                }
            }

            Row {
                spacing: 8
                PrimaryButton {
                    text: "扫描 Java"
                    filled: false
                    onClicked: {
                        App.scanJava()
                        javaCombo.model = App.getJavaRuntimes()
                    }
                }
                PrimaryButton {
                    text: "下载 Java"
                    filled: false
                    onClicked: App.downloadJava()
                }
            }

            Text { text: "JVM 参数"; color: SpectrumTheme.textMuted; font.pixelSize: 13; topPadding: 8 }
            TextField {
                id: jvmField
                width: parent.width
                text: App.getJvmArgs()
                placeholderText: "留空使用默认值"
                onEditingFinished: App.setJvmArgs(text)
            }

            PrimaryButton {
                text: "保存设置"
                width: 200
                onClicked: App.saveSettings()
            }
        }
    }

    Component.onCompleted: javaCombo.model = App.getJavaRuntimes()
}
