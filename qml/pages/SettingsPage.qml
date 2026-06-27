import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true

    function reloadJavaList() {
        javaCombo.model = App.getJavaRuntimes()
        javaList.model = App.getJavaRuntimes()
    }

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

            Text {
                text: "Java 运行时"
                color: SpectrumTheme.textMuted
                font.pixelSize: 13
                topPadding: 8
            }

            Text {
                width: parent.width
                wrapMode: Text.WordWrap
                font.pixelSize: 12
                color: SpectrumTheme.textMuted
                text: "手动添加 java.exe 路径，或将 java.exe / JDK 文件夹拖到启动器窗口任意位置。"
            }

            Row {
                spacing: 8
                width: parent.width
                TextField {
                    id: javaPathField
                    width: parent.width - 200
                    placeholderText: "C:/Program Files/Java/.../bin/java.exe"
                }
                PrimaryButton {
                    text: "浏览"
                    filled: false
                    onClicked: {
                        var p = App.browseJavaExecutable()
                        if (p)
                            javaPathField.text = p
                    }
                }
                PrimaryButton {
                    text: "添加"
                    filled: false
                    onClicked: {
                        App.addJavaPath(javaPathField.text)
                        javaPathField.text = ""
                        root.reloadJavaList()
                    }
                }
            }

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

            ListView {
                id: javaList
                width: parent.width
                height: Math.min(180, Math.max(48, count * 44))
                clip: true
                spacing: 4
                model: App.getJavaRuntimes()
                delegate: Rectangle {
                    width: javaList.width
                    height: 40
                    radius: SpectrumTheme.radiusSm
                    color: SpectrumTheme.surfaceHover
                    Row {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8
                        Text {
                            width: parent.width - 72
                            anchors.verticalCenter: parent.verticalCenter
                            text: model.label || model.path
                            font.pixelSize: 12
                            color: SpectrumTheme.text
                            clip: true
                        }
                        PrimaryButton {
                            text: "删除"
                            filled: false
                            anchors.verticalCenter: parent.verticalCenter
                            onClicked: {
                                App.removeJava(model.path)
                                root.reloadJavaList()
                            }
                        }
                    }
                }
            }

            Row {
                spacing: 8
                PrimaryButton {
                    text: "扫描 Java"
                    filled: false
                    onClicked: App.scanJava()
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

    Connections {
        target: App
        function onJavaRuntimesChanged() { root.reloadJavaList() }
    }

    Component.onCompleted: root.reloadJavaList()
}
