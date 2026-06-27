import QtQuick
import QtQuick.Layouts
import Spectrum

Item {
    Layout.fillWidth: true
    Layout.fillHeight: true

    Loader {
        anchors.fill: parent
        source: webAvailable ? "ModrinthWeb.qml" : ""
    }

    SpectrumCard {
        anchors.centerIn: parent
        width: 420
        visible: !webAvailable

        Column {
            anchors.fill: parent
            spacing: 8
            Text {
                text: "需要 PySide6-WebEngine"
                font.pixelSize: 14
                color: SpectrumTheme.textTitle
            }
            Text {
                text: "pip install PySide6-WebEngine"
                color: SpectrumTheme.textMuted
                font.pixelSize: 13
            }
        }
    }

    property bool webAvailable: hasWebEngine
}
