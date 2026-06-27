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
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
