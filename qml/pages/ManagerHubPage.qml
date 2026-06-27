import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum
import "."

Item {
    id: root
    anchors.fill: parent

    property int subIndex: tabBar.currentIndex

    onSubIndexChanged: {
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

        StackLayout {
            width: parent.width
            height: parent.height - tabBar.height - 12
            currentIndex: tabBar.currentIndex

            ManagerPage {}
            DownloadPage {}
            LabymodPage {}
        }
    }

    Component.onCompleted: App.setBackendTab(3)
}
