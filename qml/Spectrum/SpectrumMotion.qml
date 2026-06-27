pragma Singleton
import QtQuick

QtObject {
    readonly property int fast: 150
    readonly property int normal: 220
    readonly property int page: 280
    readonly property int slow: 380

    readonly property int easeOut: Easing.OutCubic
    readonly property int easeInOut: Easing.InOutCubic

    readonly property real hoverScale: 1.02
    readonly property real pressScale: 0.97
    readonly property real pageOffset: 14
    readonly property real cardOffset: 10
    readonly property int staggerStep: 70
}
