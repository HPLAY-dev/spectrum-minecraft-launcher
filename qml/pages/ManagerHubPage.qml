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
        var tabs = [3, 1, 2]
        App.setBackendTab(tabs[subIndex])
    }

    Column {
        anchors.fill: parent
        spacing: 12

        TabBar {
            id: tabBar
            width: parent.width
            TabButton { text: "管理" }
            TabButton { text: "下载" }
            TabButton { text: "LabyMod" }
        }

        Item {
            width: parent.width
            height: parent.height - tabBar.height - 12

            PageLayer {
                id: manageTab
                anchors.fill: parent
                active: tabBar.currentIndex === 0
                direction: root.tabDirection
                property bool everShown: active
                onActiveChanged: if (active) everShown = true

                Loader {
                    anchors.fill: parent
                    active: manageTab.everShown
                    asynchronous: true
                    source: "ManagerPage.qml"
                }
            }
            PageLayer {
                id: downloadTab
                anchors.fill: parent
                active: tabBar.currentIndex === 1
                direction: root.tabDirection
                property bool everShown: active
                onActiveChanged: if (active) everShown = true

                Loader {
                    anchors.fill: parent
                    active: downloadTab.everShown
                    asynchronous: true
                    source: "DownloadPage.qml"
                }
            }
            PageLayer {
                id: labyTab
                anchors.fill: parent
                active: tabBar.currentIndex === 2
                direction: root.tabDirection
                property bool everShown: active
                onActiveChanged: if (active) everShown = true

                Loader {
                    anchors.fill: parent
                    active: labyTab.everShown
                    asynchronous: true
                    source: "LabymodPage.qml"
                }
            }
        }
    }
}
