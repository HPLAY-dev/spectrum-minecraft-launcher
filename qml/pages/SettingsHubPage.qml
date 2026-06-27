import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum
import "."

Item {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true

    property int subIndex: tabBar.currentIndex

    onSubIndexChanged: {
        var tabs = [5, 4, 6]
        App.setBackendTab(tabs[subIndex])
    }

    Column {
        anchors.fill: parent
        spacing: 12

        TabBar {
            id: tabBar
            width: parent.width
            TabButton { text: "设置" }
            TabButton { text: "账户" }
            TabButton { text: "关于" }
        }

        StackLayout {
            width: parent.width
            height: parent.height - tabBar.height - 12
            currentIndex: tabBar.currentIndex

            SettingsPage {}
            AccountsPage {}
            AboutPage {}
        }
    }

    Component.onCompleted: App.setBackendTab(5)
}
