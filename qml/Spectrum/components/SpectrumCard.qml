import QtQuick
import Spectrum

Item {
    id: card
    default property alias children: contentItem.data

    property bool animateIn: false
    property int staggerIndex: 0
    property bool _revealed: !animateIn

    opacity: _revealed ? 1 : 0
    transform: Translate {
        id: cardSlide
        y: card._revealed ? 0 : SpectrumMotion.cardOffset
        Behavior on y {
            NumberAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: SpectrumMotion.normal
            easing.type: SpectrumMotion.easeOut
        }
    }

    Timer {
        interval: card.staggerIndex * SpectrumMotion.staggerStep
        running: card.animateIn && !card._revealed
        onTriggered: card._revealed = true
    }

    CutCornerBox {
        anchors.fill: parent
        cut: SpectrumTheme.cutMd
        fillColor: SpectrumTheme.surface
        borderColor: SpectrumTheme.border
        borderWidth: 1
    }

    Item {
        id: contentItem
        anchors.fill: parent
        anchors.margins: 20
    }
}
