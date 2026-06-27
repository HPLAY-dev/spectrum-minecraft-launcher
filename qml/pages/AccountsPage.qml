import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    anchors.fill: parent

    ColumnLayout {
        anchors.fill: parent
        spacing: 16

        Text {
            text: "账户"
            font.pixelSize: 22
            font.family: SpectrumTheme.fontCnTitle
            font.weight: SpectrumTheme.weightCnTitle
        }

        PrimaryButton {
            text: "Microsoft 登录 (OAuth)"
            Layout.preferredWidth: 280
            onClicked: App.oauthLogin()
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: SpectrumTheme.border
        }

        Text { text: "已保存账户"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

        ListView {
            id: accList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 120
            clip: true
            spacing: 4
            model: App.getAccounts()
            delegate: Rectangle {
                width: accList.width
                height: 48
                radius: SpectrumTheme.radiusSm
                color: SpectrumTheme.surfaceHover
                Row {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2
                        Text {
                            text: modelData.name
                            color: SpectrumTheme.text
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: modelData.type
                            color: SpectrumTheme.textMuted
                            font.pixelSize: 11
                        }
                    }
                    Item { width: parent.width - 200; height: 1 }
                    PrimaryButton {
                        text: "删除"
                        filled: false
                        anchors.verticalCenter: parent.verticalCenter
                        onClicked: App.removeAccount(index)
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            TextField {
                id: offlineName
                Layout.fillWidth: true
                placeholderText: "离线玩家名"
            }
            PrimaryButton {
                text: "添加离线"
                filled: false
                onClicked: {
                    App.addOfflineAccount(offlineName.text)
                    offlineName.text = ""
                }
            }
        }
    }

    Connections {
        target: App
        function onAccountsChanged() { accList.model = App.getAccounts() }
    }
}
