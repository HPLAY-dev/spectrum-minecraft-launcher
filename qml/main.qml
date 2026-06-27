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

    property bool javaDropActive: false

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

    function isJavaDropUrl(url) {
        var s = url.toString().toLowerCase()
        return s.indexOf("java.exe") >= 0
            || s.indexOf("javaw.exe") >= 0
            || s.indexOf("/bin/java") >= 0
            || s.indexOf("\\bin\\java") >= 0
    }

    function acceptJavaDrop(drag) {
        if (!drag.hasUrls)
            return false
        for (var i = 0; i < drag.urls.length; ++i) {
            if (isJavaDropUrl(drag.urls[i]))
                return true
        }
        return false
    }

    DropArea {
        id: javaDropArea
        anchors.fill: parent
        z: 80
        keys: ["text/uri-list"]

        onEntered: (drag) => {
            if (drag.hasUrls) {
                drag.accepted = true
                window.javaDropActive = true
            }
        }
        onExited: window.javaDropActive = false
        onDropped: (drop) => {
            window.javaDropActive = false
            if (!drop.hasUrls)
                return
            var urls = []
            for (var i = 0; i < drop.urls.length; ++i)
                urls.push(drop.urls[i])
            App.addJavaFromDropUrls(urls)
        }
    }

    CutCornerBox {
        visible: window.javaDropActive
        z: 81
        anchors.fill: parent
        anchors.margins: 12
        cut: SpectrumTheme.cutLg
        fillColor: Qt.rgba(0.72, 0.82, 0.75, 0.18)
        borderColor: SpectrumTheme.sageLight

        Text {
            anchors.centerIn: parent
            text: "释放以添加 Java"
            font.pixelSize: 18
            font.family: SpectrumTheme.fontCnTitle
            color: SpectrumTheme.textTitle
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

    LaunchConsole {
        id: launchConsole
        z: 90
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
    }

    Connections {
        target: App
        function onConsoleLog(line) { launchConsole.appendLog(line) }
        function onDownloadProgress(pct, total, desc) { launchConsole.progress = pct }
    }
}
