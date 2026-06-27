import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    Layout.fillWidth: true
    Layout.fillHeight: true

    Column {
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
            width: 280
            onClicked: App.oauthLogin()
        }

        Rectangle {
            width: parent.width
            height: 1
            color: SpectrumTheme.border
        }

        Text { text: "已保存账户"; color: SpectrumTheme.textMuted; font.pixelSize: 13 }

        ListView {
            id: accList
            width: parent.width
            height: 220
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

        Row {
            spacing: 8
            width: parent.width
            TextField {
                id: offlineName
                width: parent.width - 120
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
