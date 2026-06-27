import QtQuick
import QtQuick.Controls
import Spectrum

Item {
    id: root
    property string label: ""
    property string iconText: ""
    property bool active: false
    signal clicked()

    implicitWidth: 180
    implicitHeight: 40

    scale: mouseArea.pressed ? SpectrumMotion.pressScale
        : (mouseArea.containsMouse ? SpectrumMotion.hoverScale : 1)

    Behavior on scale {
        NumberAnimation {
            duration: SpectrumMotion.fast
            easing.type: SpectrumMotion.easeOut
        }
    }

    transformOrigin: Item.Left

    Rectangle {
        width: 3
        height: parent.height * 0.55
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        color: SpectrumTheme.accent
        opacity: root.active ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }
    }

    CutCornerBox {
        anchors.fill: parent
        cut: SpectrumTheme.cutSm
        fillColor: root.active ? SpectrumTheme.primary
            : (mouseArea.containsMouse ? SpectrumTheme.surfaceActive : SpectrumTheme.surfaceHover)
        borderColor: "transparent"
        borderWidth: 0
    }

    Text {
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        text: root.label
        font.family: SpectrumTheme.fontCnBody
        font.weight: root.active ? SpectrumTheme.weightCnTitle : SpectrumTheme.weightCnBody
        color: root.active ? SpectrumTheme.onPrimary : SpectrumTheme.text
        Behavior on color {
            ColorAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
