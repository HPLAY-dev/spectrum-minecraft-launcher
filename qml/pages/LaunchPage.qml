import QtQuick
import QtQuick.Controls
import Spectrum

Item {
    id: root
    anchors.fill: parent

    property var status: ({ instance: "未选择", memory: "4G", javaCount: 0, modCount: 0 })

    function reloadStatus() {
        try {
            status = JSON.parse(App.getLaunchStatus())
        } catch (e) {
            status = { instance: "未选择", memory: "4G", javaCount: 0, modCount: 0 }
        }
    }

    Column {
        anchors.fill: parent
        spacing: 0

        Row {
            width: parent.width
            spacing: 16

            Text {
                text: "启动器主页"
                font.family: SpectrumTheme.fontCnTitle
                font.weight: SpectrumTheme.weightCnTitle
                color: SpectrumTheme.textTitle
                anchors.verticalCenter: parent.verticalCenter
            }

            Item { width: parent.width - 400; height: 1 }

            PrimaryButton {
                text: "▶  启动游戏"
                filled: true
                cornerCut: SpectrumTheme.cutLg
                onClicked: App.launch()
            }
        }

        Item { height: 40; width: 1 }

        Row {
            width: parent.width
            spacing: 20
            layoutDirection: Qt.LeftToRight

            SpectrumCard {
                width: (parent.width - 20) / 2
                height: 280

                Column {
                    anchors.fill: parent
                    spacing: 10

                    Text {
                        text: "当前配置"
                        font.pixelSize: 14
                        color: SpectrumTheme.textMuted
                    }

                    Text {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        text: "选择 Minecraft 版本与运行环境，保持轻量化启动配置。"
                        font.pixelSize: 13
                        color: SpectrumTheme.textMuted
                        lineHeight: 1.6
                    }

                    Text {
                        text: "游戏实例"
                        font.pixelSize: 13
                        color: SpectrumTheme.textMuted
                        topPadding: 8
                    }

                    ComboBox {
                        id: instCombo
                        width: parent.width
                        model: App.getInstances()
                        onActivated: {
                            App.selectInstance(model[currentIndex])
                            root.reloadStatus()
                        }
                        Component.onCompleted: {
                            instCombo.model = App.getInstances()
                            reloadStatus()
                        }
                    }

                    Text { text: "账户"; font.pixelSize: 13; color: SpectrumTheme.textMuted }

                    ComboBox {
                        id: accountCombo
                        width: parent.width
                        model: App.getAccounts()
                        textRole: "name"
                        onActivated: App.selectAccount(currentIndex)
                    }

                    Row {
                        spacing: 12
                        width: parent.width
                        Column {
                            width: parent.width / 2 - 6
                            Text { text: "内存"; font.pixelSize: 13; color: SpectrumTheme.textMuted }
                            ComboBox {
                                id: memoryCombo
                                width: parent.width
                                model: ["2048M", "3G", "4G", "6G", "8G"]
                                Component.onCompleted: {
                                    var mem = App.getMemory()
                                    for (var i = 0; i < memoryCombo.model.length; i++) {
                                        if (memoryCombo.model[i] === mem) {
                                            memoryCombo.currentIndex = i
                                            break
                                        }
                                    }
                                }
                                onActivated: App.setMemory(model[currentIndex])
                            }
                        }
                        PrimaryButton {
                            text: "刷新"
                            filled: false
                            anchors.bottom: parent.bottom
                            onClicked: {
                                instCombo.model = App.getInstances()
                                reloadStatus()
                            }
                        }
                    }
                }
            }

            SpectrumCard {
                width: (parent.width - 20) / 2
                height: 280

                Column {
                    anchors.fill: parent
                    spacing: 10

                    Text {
                        text: "状态信息"
                        font.pixelSize: 14
                        color: SpectrumTheme.textMuted
                    }

                    Text {
                        width: parent.width
                        font.pixelSize: 13
                        color: SpectrumTheme.textMuted
                        lineHeight: 1.8
                        text: "Java：已检测 " + root.status.javaCount + " 个\n"
                            + "内存：" + root.status.memory + " 分配\n"
                            + "当前实例：" + root.status.instance + "\n"
                            + "模组：" + root.status.modCount
                    }
                }
            }
        }
    }

    Connections {
        target: App
        function onAccountsChanged() { accountCombo.model = App.getAccounts() }
        function onInstancesChanged() {
            instCombo.model = App.getInstances()
            reloadStatus()
        }
    }
}
