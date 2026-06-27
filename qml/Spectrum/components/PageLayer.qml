import QtQuick
import Spectrum

Item {
    id: root
    property bool active: false
    property int direction: 1
    default property alias content: host.data

    opacity: active ? 1 : 0
    enabled: active
    visible: opacity > 0.01 || active

    transform: Translate {
        id: slide
        y: active ? 0 : direction * SpectrumMotion.pageOffset
        Behavior on y {
            NumberAnimation {
                duration: SpectrumMotion.page
                easing.type: SpectrumMotion.easeOut
            }
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: SpectrumMotion.page
            easing.type: SpectrumMotion.easeOut
        }
    }

    Item {
        id: host
        anchors.fill: parent

        onChildrenChanged: root.bindChildren()
    }

    Component.onCompleted: bindChildren()

    function bindChildren() {
        for (var i = 0; i < host.children.length; ++i) {
            var child = host.children[i]
            child.anchors.fill = host
        }
    }
}
