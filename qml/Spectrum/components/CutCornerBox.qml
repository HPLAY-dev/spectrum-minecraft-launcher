import QtQuick
import QtQuick.Shapes
import Spectrum

Item {
    id: root
    property color fillColor: "#EEEEEE"
    property color borderColor: "#CBCBCB"
    property real borderWidth: 1
    property real cut: 6

    Behavior on fillColor {
        ColorAnimation {
            duration: SpectrumMotion.normal
            easing.type: SpectrumMotion.easeOut
        }
    }

    Behavior on borderColor {
        ColorAnimation {
            duration: SpectrumMotion.normal
            easing.type: SpectrumMotion.easeOut
        }
    }

    Shape {
        anchors.fill: parent
        ShapePath {
            strokeColor: root.borderColor
            strokeWidth: root.borderWidth
            fillColor: root.fillColor
            PathMove { x: root.cut; y: 0 }
            PathLine { x: root.width; y: 0 }
            PathLine { x: root.width; y: root.height - root.cut }
            PathLine { x: root.width - root.cut; y: root.height }
            PathLine { x: 0; y: root.height }
            PathLine { x: 0; y: root.cut }
            PathLine { x: root.cut; y: 0 }
        }
    }
}
