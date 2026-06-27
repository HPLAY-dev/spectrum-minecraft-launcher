import QtQuick
import QtWebEngine
import QtWebChannel

Item {
    anchors.fill: parent

    QtObject {
        id: modrinthBridge
        WebChannel.id: "web"

        function searchModrinth(query, loader) {
            return Web.searchModrinth(query, loader)
        }
        function installMod(index) {
            return Web.installMod(index)
        }
        function getInstances() {
            return Web.getInstances()
        }
        function getDefaultInstance() {
            return Web.getDefaultInstance()
        }
        function setTargetInstance(name) {
            Web.setTargetInstance(name)
        }
        function setTargetLoader(loader) {
            Web.setTargetLoader(loader)
        }
    }

    WebEngineView {
        id: web
        anchors.fill: parent

        settings {
            localContentCanAccessFileUrls: true
            localContentCanAccessRemoteUrls: true
        }

        webChannel: WebChannel {
            registeredObjects: [modrinthBridge]
        }

        Component.onCompleted: {
            url = App.modrinthWebUrl()
        }
    }
}
