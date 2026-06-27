pragma Singleton
import QtQuick

QtObject {
    // 色卡：#777C6D · #B7B89F · #CBCBCB · #EEEEEE
    readonly property color sage: "#777C6D"
    readonly property color sageLight: "#B7B89F"
    readonly property color gray: "#CBCBCB"
    readonly property color light: "#EEEEEE"

    readonly property color bg: light
    readonly property color surface: light
    readonly property color surfaceHover: gray
    readonly property color surfaceActive: sageLight
    readonly property color primary: sage
    readonly property color primaryHover: "#6a6f62"
    readonly property color primaryPressed: "#5f6458"
    readonly property color onPrimary: light
    readonly property color text: sage
    readonly property color textMuted: sageLight
    readonly property color textTitle: sage
    readonly property color accent: sage
    readonly property color border: gray
    readonly property color borderInput: gray
    readonly property color inputBg: light
    readonly property int cutSm: 6
    readonly property int cutMd: 8
    readonly property int cutLg: 10
    readonly property int radiusSm: 0
    readonly property int radiusMd: 0
    readonly property int radiusLg: 0

    readonly property string fontCnTitle: AppFonts.cnTitleFamily
    readonly property string fontCnBody: AppFonts.cnBodyFamily
    readonly property string fontEnTitle: AppFonts.enTitleFamily
    readonly property string fontEnBody: AppFonts.enBodyFamily
    readonly property int weightCnTitle: AppFonts.cnTitleWeight
    readonly property int weightCnBody: AppFonts.cnBodyWeight
    readonly property int weightEnTitle: AppFonts.enTitleWeight
    readonly property int weightEnBody: AppFonts.enBodyWeight

    readonly property string fontFamily: fontCnBody
}
