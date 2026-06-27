import QtQuick
import QtWebEngine
import QtWebChannel

WebEngineView {
    id: web
    url: App.modrinthWebUrl()
    anchors.fill: parent

    webChannel: WebChannel {
        id: channel
        registeredObjects: [webHost]
    }

    QtObject {
        id: webHost
        WebChannel.id: "web"

        function searchModrinth(query, loader) {
            return Web.searchModrinth(query, loader)
        }

        function installMod(index) {
            return Web.installMod(index)
        }

        function getInstances(callback) {
            callback(Web.getInstances())
        }

        function setTargetInstance(name) {
            Web.setTargetInstance(name)
        }
    }
}
