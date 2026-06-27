import QtQuick
import QtQuick.Shapes

Item {
    id: root
    property color fillColor: "#EEEEEE"
    property color borderColor: "#CBCBCB"
    property real borderWidth: 1
    property real cut: 6

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
