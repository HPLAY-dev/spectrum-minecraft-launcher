import QtQuick
import Spectrum

Item {
    id: root
    property bool active: false
    property int dotCount: 5
    readonly property int barHeight: 4

    height: active ? barHeight : 0
    clip: true
    opacity: active ? 1 : 0
    visible: height > 0 || opacity > 0.01

    Behavior on height {
        NumberAnimation { duration: SpectrumMotion.normal; easing.type: SpectrumMotion.easeOut }
    }
    Behavior on opacity {
        NumberAnimation { duration: SpectrumMotion.normal; easing.type: SpectrumMotion.easeOut }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Qt.rgba(SpectrumTheme.sage.r, SpectrumTheme.sage.g, SpectrumTheme.sage.b, 0.12)
    }

    Repeater {
        model: root.dotCount

        Item {
            id: lane
            anchors.fill: parent

            property real dotW: 5 + (index % 3) * 2
            property real dotH: 2 + (index % 2)
            property int travelMs: 900 + index * 260
            property int pauseMs: index * 140
            property real yOff: (index % 3) * 0.6
            property bool reverse: index % 2 === 1

            Rectangle {
                id: dot
                width: lane.dotW
                height: lane.dotH
                radius: height / 2
                y: lane.yOff
                color: Qt.rgba(
                    SpectrumTheme.sage.r,
                    SpectrumTheme.sage.g,
                    SpectrumTheme.sage.b,
                    0.35 + (index % 3) * 0.18
                )

                x: lane.reverse ? lane.width : -width

                SequentialAnimation {
                    id: slideAnim
                    running: root.active && lane.width > 0
                    loops: Animation.Infinite

                    PauseAnimation { duration: lane.pauseMs }

                    NumberAnimation {
                        target: dot
                        property: "x"
                        from: lane.reverse ? lane.width : -dot.width
                        to: lane.reverse ? -dot.width : lane.width
                        duration: lane.travelMs
                        easing.type: index % 3 === 0 ? Easing.InOutCubic
                            : (index % 3 === 1 ? Easing.InOutQuad : Easing.InOutSine)
                    }

                    PauseAnimation { duration: 80 + index * 30 }
                }
            }
        }
    }
}
