import QtQuick
import QtWebEngine
import QtWebChannel

WebEngineView {
    id: web
    url: App.modrinthWebUrl()
    anchors.fill: parent

    webChannel: WebChannel {
        id: channel
        registeredObjects: [Web]
    }
}
