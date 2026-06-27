import QtQuick
import QtQuick.Controls
import Spectrum

SpectrumCard {
    id: root
    anchors.fill: parent

    property string selectedInstance: ""
    property var detail: ({ saves: [], mods: [], resourcepacks: [], shaderpacks: [] })
    property int contentTab: 0

    function reloadDetail() {
        if (!selectedInstance) {
            detail = { saves: [], mods: [], resourcepacks: [], shaderpacks: [] }
            return
        }
        try {
            detail = JSON.parse(App.getManagerDetail(selectedInstance))
        } catch (e) {
            detail = { saves: [], mods: [], resourcepacks: [], shaderpacks: [] }
        }
    }

    function currentItems() {
        if (contentTab === 0) return detail.saves || []
        if (contentTab === 1) return detail.mods || []
        if (contentTab === 2) return detail.resourcepacks || []
        return detail.shaderpacks || []
    }

    function deleteKind() {
        if (contentTab === 0) return "save"
        if (contentTab === 1) return "mod"
        if (contentTab === 2) return "respack"
        return "shader"
    }

    Column {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "版本管理"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        Row {
            spacing: 16
            width: parent.width
            height: parent.height - 48

            Column {
                width: parent.width * 0.32
                spacing: 8

                Text { text: "已安装实例"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

                ListView {
                    id: instList
                    width: parent.width
                    height: 320
                    clip: true
                    spacing: 4
                    model: App.getInstances()
                    currentIndex: -1
                    delegate: Rectangle {
                        width: instList.width
                        height: 40
                        radius: SpectrumTheme.radiusSm
                        color: instList.currentIndex === index ? SpectrumTheme.primary : SpectrumTheme.surfaceHover
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: instList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.text
                            font.pixelSize: 13
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                instList.currentIndex = index
                                root.selectedInstance = modelData
                                root.reloadDetail()
                            }
                        }
                    }
                    Component.onCompleted: App.refreshInstances()
                }

                Row {
                    spacing: 6
                    width: parent.width
                    PrimaryButton {
                        text: "刷新"
                        filled: false
                        onClicked: {
                            instList.model = App.getInstances()
                            if (root.selectedInstance)
                                root.reloadDetail()
                        }
                    }
                    PrimaryButton {
                        text: "打开目录"
                        filled: false
                        enabled: root.selectedInstance !== ""
                        onClicked: App.openInstanceFolder(root.selectedInstance)
                    }
                }
            }

            Column {
                width: parent.width * 0.64
                spacing: 10

                Row {
                    spacing: 8
                    width: parent.width
                    TextField {
                        id: renameField
                        width: parent.width - 280
                        placeholderText: "新实例名称"
                        enabled: root.selectedInstance !== ""
                    }
                    PrimaryButton {
                        text: "重命名"
                        filled: false
                        enabled: root.selectedInstance !== "" && renameField.text.length > 0
                        onClicked: {
                            App.renameInstance(root.selectedInstance, renameField.text)
                            instList.model = App.getInstances()
                            root.selectedInstance = renameField.text
                            renameField.text = ""
                            root.reloadDetail()
                        }
                    }
                    PrimaryButton {
                        text: "删除实例"
                        filled: false
                        enabled: root.selectedInstance !== ""
                        onClicked: {
                            var name = root.selectedInstance
                            App.deleteInstance(name)
                            instList.model = App.getInstances()
                            root.selectedInstance = ""
                            root.reloadDetail()
                        }
                    }
                }

                TabBar {
                    id: tabs
                    width: parent.width
                    currentIndex: root.contentTab
                    onCurrentIndexChanged: root.contentTab = currentIndex
                    TabButton { text: "存档" }
                    TabButton { text: "Mods" }
                    TabButton { text: "资源包" }
                    TabButton { text: "光影" }
                }

                ListView {
                    id: contentList
                    width: parent.width
                    height: 260
                    clip: true
                    spacing: 2
                    model: root.currentItems()
                    delegate: Rectangle {
                        width: contentList.width
                        height: 36
                        radius: 4
                        color: contentList.currentIndex === index ? SpectrumTheme.primary : "transparent"
                        Row {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 8
                            Text {
                            text: modelData
                            color: contentList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.text
                                font.pixelSize: 13
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width - 80
                                elide: Text.ElideRight
                            }
                            PrimaryButton {
                                text: "删除"
                                filled: false
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: {
                                    App.deleteManagerItem(root.deleteKind(), root.selectedInstance, modelData)
                                    root.reloadDetail()
                                }
                            }
                        }
                    }
                }

                Text {
                    visible: root.selectedInstance === ""
                    text: "← 选择左侧实例以管理内容"
                    color: SpectrumTheme.textMuted
                    font.pixelSize: 13
                }
            }
        }
    }

    Connections {
        target: App
        function onManagerDataChanged() { root.reloadDetail() }
        function onInstancesChanged() { instList.model = App.getInstances() }
    }
}
