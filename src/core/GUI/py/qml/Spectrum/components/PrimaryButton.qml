import QtQuick
import QtQuick.Controls
import Spectrum

Button {
    id: control
    property bool filled: true

    background: Rectangle {
        radius: SpectrumTheme.radiusSm
        color: control.filled
            ? (control.down ? Qt.darker(SpectrumTheme.primary, 1.1) : SpectrumTheme.primary)
            : "transparent"
        border.color: SpectrumTheme.primary
        border.width: control.filled ? 0 : 1
    }

    contentItem: Text {
        text: control.text
        color: control.filled ? SpectrumTheme.onPrimary : SpectrumTheme.primary
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    padding: 10
    leftPadding: 16
    rightPadding: 16
}
