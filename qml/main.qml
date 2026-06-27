import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum
import "pages"

ApplicationWindow {
    id: window
    width: 1100
    height: 680
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    title: "Spectrum-Minecraft-Launcher"
    color: SpectrumTheme.bg
    font.family: SpectrumTheme.fontCnBody
    font.weight: SpectrumTheme.weightCnBody

    property int navIndex: 0
    property string toastText: ""
    property string toastLevel: ""
    property bool toastVisible: false

    readonly property var navItems: [
        "启动", "版本管理", "模组", "设置"
    ]

    function showToast(msg, level) {
        toastText = msg
        toastLevel = level || "ok"
        toastVisible = true
        toastTimer.restart()
    }

    Timer {
        id: toastTimer
        interval: 3200
        onTriggered: toastVisible = false
    }

    Connections {
        target: App
        function onToast(msg, level) { window.showToast(msg, level) }
    }

    CutCornerBox {
        visible: toastVisible
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        cut: SpectrumTheme.cutSm
        width: toastLabel.implicitWidth + 32
        height: 40
        fillColor: toastLevel === "error" ? SpectrumTheme.surfaceActive : (toastLevel === "warn" ? SpectrumTheme.surfaceHover : SpectrumTheme.surface)
        borderColor: SpectrumTheme.border

        Text {
            id: toastLabel
            anchors.centerIn: parent
            text: toastText
            color: SpectrumTheme.text
            font.pixelSize: 13
            font.family: SpectrumTheme.fontCnBody
            font.weight: SpectrumTheme.weightCnBody
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            color: SpectrumTheme.surface

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: SpectrumTheme.border
            }

            Column {
                anchors.fill: parent
                anchors.margins: 20
                anchors.topMargin: 30
                spacing: 10

                Text {
                    text: "Spectrum-Minecraft-Launcher"
                    width: parent.width
                    wrapMode: Text.Wrap
                    font.family: SpectrumTheme.fontEnTitle
                    font.weight: SpectrumTheme.weightEnTitle
                    font.pixelSize: 12
                    color: SpectrumTheme.accent
                    bottomPadding: 24
                }

                Repeater {
                    model: window.navItems
                    delegate: NavItem {
                        label: modelData
                        active: window.navIndex === index
                        onClicked: {
                            window.navIndex = index
                            App.setCurrentPage(index)
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: SpectrumTheme.bg

            StackLayout {
                anchors.fill: parent
                anchors.margins: 40
                currentIndex: window.navIndex

                LaunchPage {}
                ManagerHubPage {}
                ModrinthPage {}
                SettingsHubPage {}
            }
        }
    }
}
