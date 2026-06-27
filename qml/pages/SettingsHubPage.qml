import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum
import "."

Item {
    id: root
    anchors.fill: parent

    property int subIndex: tabBar.currentIndex
    property int tabDirection: 1
    property int _prevTab: 0

    onSubIndexChanged: {
        tabDirection = subIndex > _prevTab ? 1 : -1
        _prevTab = subIndex
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

        Item {
            width: parent.width
            height: parent.height - tabBar.height - 12

            PageLayer {
                anchors.fill: parent
                active: tabBar.currentIndex === 0
                direction: root.tabDirection
                SettingsPage {}
            }
            PageLayer {
                anchors.fill: parent
                active: tabBar.currentIndex === 1
                direction: root.tabDirection
                AccountsPage {}
            }
            PageLayer {
                anchors.fill: parent
                active: tabBar.currentIndex === 2
                direction: root.tabDirection
                AboutPage {}
            }
        }
    }

    Component.onCompleted: App.setBackendTab(5)
}
