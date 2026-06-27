import QtQuick
import QtQuick.Controls
import Spectrum

SpectrumCard {
    anchors.fill: parent

    Column {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "下载"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        Row {
            spacing: 16
            width: parent.width
            height: parent.height - 80

            Column {
                width: parent.width * 0.45
                spacing: 6
                Text { text: "版本列表"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

                ListView {
                    id: versionList
                    width: parent.width
                    height: 300
                    clip: true
                    spacing: 2
                    model: App.getVersionList()
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
                            onClicked: {
                                versionList.currentIndex = index
                                App.selectDownloadVersion(index)
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
                    versionList.model = App.getVersionList()
                }
            }

            Column {
                width: parent.width * 0.5
                spacing: 10

                Text { text: "实例名称"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                TextField {
                    id: instanceField
                    width: parent.width
                    placeholderText: "my-instance"
                    onTextChanged: App.setInstanceName(text)
                }

                Text { text: "Mod 加载器"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }
                ComboBox {
                    id: loaderCombo
                    width: parent.width
                    model: ["无", "fabric", "forge", "neoforge"]
                    onActivated: App.setModloader(model[currentIndex])
                }

                Text { text: "下载进度"; color: SpectrumTheme.textMuted; font.pixelSize: 13; topPadding: 8 }
                ProgressBar { id: progMain; width: parent.width; from: 0; to: 100; value: 0 }
                ProgressBar { id: progAst; width: parent.width; from: 0; to: 100; value: 0 }

                PrimaryButton {
                    text: "开始下载"
                    width: parent.width
                    onClicked: App.download()
                }
            }
        }
    }

    Connections {
        target: App
        function onDownloadProgress(pct, total, desc) {
            if (desc.indexOf("AST") >= 0) progAst.value = pct
            else progMain.value = pct
        }
    }
}
