import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    id: root
    readonly property int elideRight: 3
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

    function reloadInstances() {
        instModel.clear()
        var items = App.getInstances()
        for (var i = 0; i < items.length; ++i) {
            var item = items[i]
            var name = item.name || item
            var label = item.label || name
            instModel.append({ "name": name, "label": label })
        }
    }

    ListModel { id: instModel }

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "版本管理"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            ColumnLayout {
                Layout.preferredWidth: Math.round(root.width * 0.30)
                Layout.fillHeight: true
                spacing: 8

                Text { text: "已安装实例"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

                ListView {
                    id: instList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: instModel
                    currentIndex: -1
                    delegate: Rectangle {
                        width: instList.width
                        height: 48
                        radius: SpectrumTheme.radiusSm
                        color: instList.currentIndex === index ? SpectrumTheme.primary : SpectrumTheme.surfaceHover
                        scale: instList.currentIndex === index ? 1 : (mouseArea.containsMouse ? 1.01 : 1)
                        Behavior on color {
                            ColorAnimation { duration: SpectrumMotion.normal; easing.type: SpectrumMotion.easeOut }
                        }
                        Behavior on scale {
                            NumberAnimation { duration: SpectrumMotion.fast; easing.type: SpectrumMotion.easeOut }
                        }
                        Column {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            spacing: 2
                            Text {
                                text: model.name
                                color: instList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.text
                                font.pixelSize: 13
                                font.weight: Font.Medium
                            }
                            Text {
                                visible: model.label && model.label !== model.name
                                text: model.label || ""
                                color: instList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.textMuted
                                font.pixelSize: 11
                                opacity: 0.85
                            }
                        }
                        MouseArea {
                            id: mouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                instList.currentIndex = index
                                root.selectedInstance = model.name
                                root.reloadDetail()
                            }
                        }
                    }
                    Component.onCompleted: {
                        root.reloadInstances()
                        App.refreshInstances()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    PrimaryButton {
                        text: "刷新"
                        filled: false
                        onClicked: {
                            App.refreshInstances()
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

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    TextField {
                        id: renameField
                        Layout.fillWidth: true
                        placeholderText: "新实例名称"
                        enabled: root.selectedInstance !== ""
                    }
                    PrimaryButton {
                        text: "重命名"
                        filled: false
                        enabled: root.selectedInstance !== "" && renameField.text.length > 0
                        onClicked: {
                            App.renameInstance(root.selectedInstance, renameField.text)
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
                            root.selectedInstance = ""
                            root.reloadDetail()
                        }
                    }
                }

                TabBar {
                    id: tabs
                    Layout.fillWidth: true
                    currentIndex: root.contentTab
                    onCurrentIndexChanged: root.contentTab = currentIndex
                    TabButton { text: "存档" }
                    TabButton { text: "Mods" }
                    TabButton { text: "资源包" }
                    TabButton { text: "光影" }
                }

                ListView {
                    id: contentList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 2
                    model: root.currentItems()
                    delegate: Rectangle {
                        width: contentList.width
                        height: 36
                        radius: 4
                        color: contentList.currentIndex === index ? SpectrumTheme.primary : "transparent"
                        Behavior on color {
                            ColorAnimation { duration: SpectrumMotion.normal; easing.type: SpectrumMotion.easeOut }
                        }
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
                                elide: root.elideRight
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
        function onInstancesChanged() { root.reloadInstances() }
    }
}
