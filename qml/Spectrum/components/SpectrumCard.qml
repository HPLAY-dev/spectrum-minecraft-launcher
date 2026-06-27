import QtQuick
import Spectrum

Item {
    id: card
    default property alias children: contentItem.data

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
