import QtQuick
import QtQuick.Controls
import Spectrum

Button {
    id: control
    property bool filled: false
    property real cornerCut: SpectrumTheme.cutLg

    implicitHeight: filled ? 55 : 40
    implicitWidth: Math.max(filled ? 180 : 100, contentItem.implicitWidth + 32)
    font.family: AppFonts.familyFor(control.text, false)
    font.weight: AppFonts.weightFor(control.text, false)
    font.pixelSize: filled ? 16 : 14

    scale: !control.enabled ? 1
        : (control.pressed ? SpectrumMotion.pressScale
            : (control.hovered ? SpectrumMotion.hoverScale : 1))

    Behavior on scale {
        NumberAnimation {
            duration: SpectrumMotion.fast
            easing.type: SpectrumMotion.easeOut
        }
    }

    background: CutCornerBox {
        cut: control.cornerCut
        fillColor: {
            if (!control.enabled) return SpectrumTheme.surfaceHover
            if (control.filled) {
                if (control.pressed) return SpectrumTheme.primaryPressed
                if (control.hovered) return SpectrumTheme.primaryHover
                return SpectrumTheme.primary
            }
            if (control.pressed) return SpectrumTheme.surfaceActive
            if (control.hovered) return SpectrumTheme.surfaceHover
            return SpectrumTheme.surface
        }
        borderColor: control.filled ? SpectrumTheme.primary : SpectrumTheme.border
        borderWidth: 1
    }

    contentItem: Text {
        text: control.text
        font: control.font
        color: {
            if (!control.enabled) return SpectrumTheme.textMuted
            if (control.filled) return SpectrumTheme.onPrimary
            return SpectrumTheme.text
        }
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        Behavior on color {
            ColorAnimation {
                duration: SpectrumMotion.normal
                easing.type: SpectrumMotion.easeOut
            }
        }
    }
}
