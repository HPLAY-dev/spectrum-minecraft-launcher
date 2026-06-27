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
    title: "Serena Launcher"
    color: SpectrumTheme.bg
    font.family: SpectrumTheme.fontCnBody
    font.weight: SpectrumTheme.weightCnBody

    property int navIndex: 0
    property var brand: ({})
    property string toastText: ""
    property string toastLevel: ""
    property bool toastVisible: false

    property bool javaDropActive: false
    property int navDirection: 1
    property int _prevNavIndex: 0
    property real shellOpacity: 0

    readonly property var navItems: [
        "启动", "版本管理", "模组", "设置"
    ]

    function showToast(msg, level) {
        toastText = msg
        toastLevel = level || "ok"
        toastVisible = true
        toastTimer.restart()
    }

    function reloadBrand() {
        try {
            brand = JSON.parse(App.getBranding())
            title = (brand.displayName || "Serena Launcher")
                + " " + (brand.fullVersion || brand.versionRelease || "")
        } catch (e) {
            brand = {}
        }
    }

    Component.onCompleted: {
        reloadBrand()
        shellFadeIn.start()
    }

    NumberAnimation {
        id: shellFadeIn
        target: window
        property: "shellOpacity"
        from: 0
        to: 1
        duration: SpectrumMotion.slow
        easing.type: SpectrumMotion.easeOut
    }

    onNavIndexChanged: {
        navDirection = navIndex > _prevNavIndex ? 1 : -1
        _prevNavIndex = navIndex
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

    Win10TopProgress {
        id: startupProgress
        z: 200
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        active: App.startupLoading
    }

    CutCornerBox {
        id: toastBox
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: toastVisible ? 24 : 10
        opacity: toastVisible ? 1 : 0
        visible: opacity > 0.01 || toastVisible
        cut: SpectrumTheme.cutSm
        width: toastLabel.implicitWidth + 32
        height: 40
        fillColor: toastLevel === "error" ? SpectrumTheme.surfaceActive : (toastLevel === "warn" ? SpectrumTheme.surfaceHover : SpectrumTheme.surface)
        borderColor: SpectrumTheme.border

        Behavior on opacity {
            NumberAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }
        Behavior on anchors.bottomMargin {
            NumberAnimation {
                duration: SpectrumMotion.page
                easing.type: SpectrumMotion.easeOut
            }
        }

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
        z: 81
        anchors.fill: parent
        anchors.margins: 12
        opacity: window.javaDropActive ? 1 : 0
        visible: opacity > 0.01 || window.javaDropActive
        cut: SpectrumTheme.cutLg
        fillColor: Qt.rgba(0.72, 0.82, 0.75, 0.18)
        borderColor: SpectrumTheme.sageLight

        Behavior on opacity {
            NumberAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }

        Text {
            anchors.centerIn: parent
            text: "释放以添加 Java"
            font.pixelSize: 18
            font.family: SpectrumTheme.fontCnTitle
            color: SpectrumTheme.textTitle
            opacity: window.javaDropActive ? 1 : 0
            scale: window.javaDropActive ? 1 : 0.96
            Behavior on opacity {
                NumberAnimation { duration: SpectrumMotion.normal; easing.type: SpectrumMotion.easeOut }
            }
            Behavior on scale {
                NumberAnimation { duration: SpectrumMotion.page; easing.type: SpectrumMotion.easeOut }
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        opacity: window.shellOpacity

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
                    text: brand.displayName || "Serena Launcher"
                    width: parent.width
                    wrapMode: Text.Wrap
                    font.family: SpectrumTheme.fontEnTitle
                    font.weight: SpectrumTheme.weightEnTitle
                    font.pixelSize: 12
                    color: SpectrumTheme.accent
                    bottomPadding: 4
                }

                Text {
                    visible: brand.codename
                    text: brand.codename + " · " + (brand.versionRelease || "")
                    width: parent.width
                    wrapMode: Text.Wrap
                    font.pixelSize: 10
                    color: SpectrumTheme.textMuted
                    bottomPadding: 20
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

            Item {
                anchors.fill: parent

                PageLayer {
                    id: launchLayer
                    anchors.fill: parent
                    anchors.margins: 28
                    active: window.navIndex === 0
                    direction: window.navDirection
                    property bool everShown: active
                    onActiveChanged: if (active) everShown = true

                    Loader {
                        anchors.fill: parent
                        active: launchLayer.everShown
                        asynchronous: true
                        source: "pages/LaunchPage.qml"
                    }
                }
                PageLayer {
                    id: managerLayer
                    anchors.fill: parent
                    anchors.margins: 28
                    active: window.navIndex === 1
                    direction: window.navDirection
                    property bool everShown: active
                    onActiveChanged: if (active) everShown = true

                    Loader {
                        anchors.fill: parent
                        active: managerLayer.everShown
                        asynchronous: true
                        source: "pages/ManagerHubPage.qml"
                    }
                }
                PageLayer {
                    id: modrinthLayer
                    anchors.fill: parent
                    anchors.margins: 28
                    active: window.navIndex === 2
                    direction: window.navDirection
                    property bool everShown: active
                    onActiveChanged: {
                        if (active) {
                            everShown = true
                            App.ensureWebEngine()
                        }
                    }

                    Loader {
                        anchors.fill: parent
                        active: modrinthLayer.everShown && App.webEngineReady
                        asynchronous: true
                        source: App.webEngineReady ? "pages/ModrinthPage.qml" : ""
                    }
                }
                PageLayer {
                    id: settingsLayer
                    anchors.fill: parent
                    anchors.margins: 28
                    active: window.navIndex === 3
                    direction: window.navDirection
                    property bool everShown: active
                    onActiveChanged: if (active) everShown = true

                    Loader {
                        anchors.fill: parent
                        active: settingsLayer.everShown
                        asynchronous: true
                        source: "pages/SettingsHubPage.qml"
                    }
                }
            }
        }
    }

    LaunchConsole {
        id: launchConsole
        z: 90
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 20
        opacity: window.shellOpacity
    }

    Connections {
        target: App
        function onConsoleLog(line) { launchConsole.appendLog(line) }
        function onDownloadProgress(pct, total, desc) { launchConsole.progress = pct }
    }
}
