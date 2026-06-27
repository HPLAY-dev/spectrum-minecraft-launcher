import QtQuick
import QtQuick.Controls
import Spectrum

Item {
    id: root
    width: expanded ? 360 : 132
    implicitHeight: expanded ? (column.implicitHeight + 40) : 36

    readonly property int elideRight: 3
    property int progress: 0
    property int maxLogLines: 8
    property bool expanded: false

    Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

    function appendLog(line) {
        if (!line)
            return
        if (logModel.count >= maxLogLines)
            logModel.remove(0)
        logModel.append({ "line": line })
        if (expanded)
            logView.positionViewAtEnd()
    }

    ListModel { id: logModel }

    CutCornerBox {
        anchors.fill: parent
        cut: SpectrumTheme.cutLg
        fillColor: Qt.rgba(1, 1, 1, 0.92)
        borderColor: SpectrumTheme.border
    }

    MouseArea {
        anchors.fill: parent
        onClicked: expanded = !expanded
        cursorShape: Qt.PointingHandCursor
    }

    Text {
        id: headerTitle
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 10
        text: expanded ? "运行日志" : "日志"
        font.pixelSize: 12
        font.family: SpectrumTheme.fontCnBody
        color: SpectrumTheme.textMuted
    }

    Text {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        text: progress > 0 && !expanded ? (progress + "%  ▸") : (expanded ? "▾" : "▸")
        font.pixelSize: 11
        font.family: SpectrumTheme.fontEnBody
        color: progress > 0 && !expanded ? SpectrumTheme.sageLight : SpectrumTheme.textMuted
    }

    Column {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: headerTitle.bottom
        anchors.margins: 4
        anchors.topMargin: 8
        spacing: 10
        visible: expanded

        ListView {
            id: logView
            width: parent.width
            height: 90
            clip: true
            model: logModel
            spacing: 2

            delegate: Text {
                width: logView.width
                text: model.line
                font.pixelSize: 12
                font.family: SpectrumTheme.fontEnBody
                color: SpectrumTheme.textMuted
                elide: root.elideRight
            }
        }

        Item {
            width: parent.width
            height: 6

            CutCornerBox {
                anchors.fill: parent
                cut: 6
                fillColor: SpectrumTheme.gray
                borderWidth: 0
            }

            Item {
                width: Math.max(0, Math.min(parent.width, parent.width * root.progress / 100))
                height: parent.height
                Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }

                CutCornerBox {
                    anchors.fill: parent
                    cut: 6
                    fillColor: SpectrumTheme.sageLight
                    borderWidth: 0
                }
            }
        }
    }
}
