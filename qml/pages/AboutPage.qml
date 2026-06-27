import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    Layout.fillWidth: true
    Layout.fillHeight: true

    Column {
        anchors.fill: parent
        spacing: 12

        Text {
            text: "Spectrum-Minecraft-Launcher"
            font.pixelSize: 28
            font.family: SpectrumTheme.fontEnTitle
            font.weight: SpectrumTheme.weightEnTitle
        }

        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: SpectrumTheme.textMuted
            font.pixelSize: 14
            lineHeight: 1.5
            text: "轻量开源 Minecraft 启动器。\nUI：QML + QSS + Vue 混合架构。\n支持 Fabric / Forge / NeoForge / LabyMod / Modrinth / 正版登录。"
        }

        Text {
            color: SpectrumTheme.primary
            font.pixelSize: 13
            text: "github.com/HPLAY-dev/spectrum-minecraft-launcher"
            font.underline: true
        }
    }
}
