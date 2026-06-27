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
            text: "下载"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            ColumnLayout {
                Layout.preferredWidth: Math.round(root.width * 0.42)
                Layout.fillHeight: true
                spacing: 6

                Text { text: "版本列表"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: versionList
                        anchors.fill: parent
                        clip: true
                        spacing: 2
                        model: App.getVersionList()
                    highlight: Rectangle {
                        radius: 4
                        color: SpectrumTheme.primary
                        opacity: 0.25
                    }
                    onCurrentIndexChanged: {
                        if (currentIndex >= 0)
                            App.selectDownloadVersion(currentIndex)
                    }
                    delegate: Rectangle {
                        width: versionList.width
                        height: 36
                        radius: 4
                        color: versionList.currentIndex === index ? SpectrumTheme.primary : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            text: modelData
                            color: versionList.currentIndex === index ? SpectrumTheme.onPrimary : SpectrumTheme.text
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: versionList.currentIndex = index
                        }
                    }
                    }
                }

                Row {
                    spacing: 8
                    CheckBox { id: cbBmcl; text: "BMCLAPI"; checked: true; onCheckedChanged: filterChanged() }
                    CheckBox { id: cbSnap; text: "快照"; onCheckedChanged: filterChanged() }
                    CheckBox { id: cbAlpha; text: "旧版 Alpha"; onCheckedChanged: filterChanged() }
                    CheckBox { id: cbBeta; text: "旧版 Beta"; onCheckedChanged: filterChanged() }
                }
                function filterChanged() {
                    App.setVersionFilters(cbBmcl.checked, cbSnap.checked, cbAlpha.checked, cbBeta.checked)
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                Text { text: "实例名称"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                TextField {
                    id: instanceField
                    Layout.fillWidth: true
                    placeholderText: "my-instance"
                    onTextChanged: App.setInstanceName(text)
                }

                Text { text: "Mod 加载器"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                ComboBox {
                    id: loaderCombo
                    Layout.fillWidth: true
                    model: ["无", "fabric", "forge", "neoforge"]
                    onActivated: App.setModloader(model[currentIndex])
                }

                Text { text: "下载进度"; color: SpectrumTheme.textMuted; font.pixelSize: 13; topPadding: 8 }
                ProgressBar { id: progMain; Layout.fillWidth: true; from: 0; to: 100; value: 0 }
                ProgressBar { id: progAst; Layout.fillWidth: true; from: 0; to: 100; value: 0 }

                PrimaryButton {
                    text: "开始下载"
                    Layout.fillWidth: true
                    enabled: versionList.currentIndex >= 0
                    onClicked: {
                        if (versionList.currentIndex < 0) {
                            return
                        }
                        App.selectDownloadVersion(versionList.currentIndex)
                        App.download()
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    Connections {
        target: App
        function onDownloadProgress(pct, total, desc) {
            if (desc.indexOf("AST") >= 0) progAst.value = pct
            else progMain.value = pct
        }
        function onDownloadFinished(ok, name) {
            progMain.value = ok ? 100 : 0
            progAst.value = ok ? 100 : 0
            versionList.model = App.getVersionList()
        }
        function onVersionsChanged() {
            var sel = App.getSelectedDownloadVersion()
            versionList.model = App.getVersionList()
            if (sel) {
                for (var i = 0; i < versionList.model.length; i++) {
                    if (versionList.model[i] === sel) {
                        versionList.currentIndex = i
                        break
                    }
                }
            }
        }
    }

    Component.onCompleted: {
        if (versionList.count === 0)
            versionList.model = App.getVersionList()
    }
}
