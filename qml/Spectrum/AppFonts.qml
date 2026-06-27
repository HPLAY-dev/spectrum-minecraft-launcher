pragma Singleton
import QtQuick

Item {
    id: root

    function fontUrl(rel) {
        return fontsDir + rel
    }

    FontLoader {
        id: playfairBold
        source: root.fontUrl("Playfair_Display/static/PlayfairDisplay-Bold.ttf")
    }

    FontLoader {
        id: loraRegular
        source: root.fontUrl("Lora/static/Lora-Regular.ttf")
    }

    FontLoader {
        id: cnRegular
        source: root.fontUrl("SiYuanSongTiRegular/SourceHanSerifCN-Regular-1.otf")
    }

    FontLoader {
        id: cnSemiBold
        source: root.fontUrl("SiYuanSongTiRegular/SourceHanSerifCN-SemiBold-7.otf")
    }

    readonly property string cnTitleFamily: cnSemiBold.status === FontLoader.Ready ? cnSemiBold.name : _cnSerif
    readonly property string cnBodyFamily: cnRegular.status === FontLoader.Ready ? cnRegular.name : _cnSerif
    readonly property string enTitleFamily: playfairBold.status === FontLoader.Ready ? playfairBold.name : "Playfair Display"
    readonly property string enBodyFamily: loraRegular.status === FontLoader.Ready ? loraRegular.name : "Lora"

    readonly property string _cnSerif: "Source Han Serif CN, Noto Serif SC, SimSun, serif"

    readonly property int cnTitleWeight: Font.DemiBold
    readonly property int cnBodyWeight: Font.Normal
    readonly property int enTitleWeight: Font.Bold
    readonly property int enBodyWeight: Font.Normal

    function isMostlyLatin(text) {
        if (!text || text.length === 0)
            return false
        var latin = 0
        for (var i = 0; i < text.length; i++) {
            var c = text.charCodeAt(i)
            if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122) || (c >= 48 && c <= 57) || c === 45)
                latin++
        }
        return latin / text.length > 0.5
    }

    function familyFor(text, asTitle) {
        if (isMostlyLatin(text))
            return asTitle ? enTitleFamily : enBodyFamily
        return asTitle ? cnTitleFamily : cnBodyFamily
    }

    function weightFor(text, asTitle) {
        if (isMostlyLatin(text))
            return asTitle ? enTitleWeight : enBodyWeight
        return asTitle ? cnTitleWeight : cnBodyWeight
    }
}
