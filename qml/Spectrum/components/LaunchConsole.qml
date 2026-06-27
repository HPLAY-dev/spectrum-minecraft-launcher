import QtQuick
import QtQuick.Controls
import Spectrum

Item {
    id: root
    width: 360
    implicitHeight: column.implicitHeight + 28

    property int progress: 0
    property int maxLogLines: 8

    function appendLog(line) {
        if (!line)
            return
        if (logModel.count >= maxLogLines)
            logModel.remove(0)
        logModel.append({ "line": line })
        logView.positionViewAtEnd()
    }

    ListModel { id: logModel }

    CutCornerBox {
        anchors.fill: parent
        cut: SpectrumTheme.cutLg
        fillColor: Qt.rgba(1, 1, 1, 0.92)
        borderColor: SpectrumTheme.border
    }

    Column {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 14
        spacing: 10

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
                elide: Text.ElRight
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
