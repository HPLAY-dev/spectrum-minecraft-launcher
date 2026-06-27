import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

Item {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true

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
                height: 360

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
                            javaCombo.reloadForInstance(model[currentIndex])
                            root.reloadStatus()
                        }
                        Component.onCompleted: {
                            App.refreshInstances()
                            instCombo.model = App.getInstances()
                            accountCombo.model = App.getAccounts()
                            reloadStatus()
                            if (instCombo.currentIndex >= 0 && instCombo.model.length > 0)
                                javaCombo.reloadForInstance(instCombo.model[instCombo.currentIndex])
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

                    Text { text: "Java 运行时"; font.pixelSize: 13; color: SpectrumTheme.textMuted; topPadding: 4 }

                    ComboBox {
                        id: javaCombo
                        width: parent.width
                        textRole: "label"
                        valueRole: "path"
                        enabled: count > 0
                        onActivated: {
                            if (currentIndex >= 0 && model[currentIndex])
                                App.selectLaunchJava(model[currentIndex].path)
                        }

                        function reloadForInstance(instanceName) {
                            if (!instanceName) {
                                model = []
                                return
                            }
                            try {
                                var all = JSON.parse(App.getJavaOptionsForInstance(instanceName))
                                var enabled = []
                                for (var i = 0; i < all.length; i++) {
                                    if (all[i].enabled)
                                        enabled.push(all[i])
                                }
                                model = enabled.length ? enabled : all
                            } catch (e) {
                                model = []
                            }
                            var pick = -1
                            for (var j = 0; j < model.length; j++) {
                                if (model[j].enabled !== false) {
                                    if (model[j].recommended) {
                                        pick = j
                                        break
                                    }
                                    if (pick < 0)
                                        pick = j
                                }
                            }
                            currentIndex = pick
                            if (pick >= 0)
                                App.selectLaunchJava(model[pick].path)
                        }
                    }

                    CheckBox {
                        id: ignoreJavaWarn
                        text: "忽略 Java 兼容警告"
                        checked: App.getIgnoreJavaWarnings()
                        onCheckedChanged: App.setIgnoreJavaWarnings(checked)
                        font.pixelSize: 12
                    }

                    Text {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        visible: root.status.minJava > 0 && root.status.mcVersion
                        font.pixelSize: 11
                        color: SpectrumTheme.textMuted
                        text: root.status.mcVersion
                            ? (root.status.java8Only
                                ? ("MC " + root.status.mcVersion + " · 仅支持 Java 8")
                                : ("MC " + root.status.mcVersion + " · 最低 Java " + root.status.minJava))
                            : ""
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
                height: 360

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
                        text: "Java：已检测 " + root.status.javaCount + " 个"
                            + (root.status.java8Only ? "（仅 Java 8）" : (root.status.minJava ? "（需要 ≥" + root.status.minJava + "）" : "")) + "\n"
                            + "内存：" + root.status.memory + " 分配\n"
                            + "当前实例：" + root.status.instance + "\n"
                            + (root.status.mcVersion ? ("MC 版本：" + root.status.mcVersion + "\n") : "")
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
            if (instCombo.currentIndex >= 0 && instCombo.model.length > 0)
                javaCombo.reloadForInstance(instCombo.model[instCombo.currentIndex])
        }
        function onJavaRuntimesChanged() {
            if (instCombo.currentIndex >= 0 && instCombo.model.length > 0)
                javaCombo.reloadForInstance(instCombo.model[instCombo.currentIndex])
            reloadStatus()
        }
    }
}
