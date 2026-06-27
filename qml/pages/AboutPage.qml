import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Spectrum

SpectrumCard {
    id: root
    anchors.fill: parent

    property var brand: ({})

    function reloadBrand() {
        try {
            brand = JSON.parse(App.getBranding())
        } catch (e) {
            brand = {}
        }
    }

    Component.onCompleted: reloadBrand()

    Column {
        anchors.fill: parent
        spacing: 12

        Text {
            text: brand.displayName || brand.projectName || "Serena Launcher"
            font.pixelSize: 28
            font.family: SpectrumTheme.fontEnTitle
            font.weight: SpectrumTheme.weightEnTitle
        }

        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: SpectrumTheme.primary
            font.pixelSize: 14
            text: brand.tagline ? ("标号：" + brand.tagline) : ""
        }

        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: SpectrumTheme.textMuted
            font.pixelSize: 14
            lineHeight: 1.6
            text: "轻量开源 Minecraft 启动器 · 项目更新 SerenaLauncher\n"
                + "开发代号：" + (brand.codename || "Okra") + "\n"
                + "版本 " + (brand.versionRelease || "26.2")
                + " · " + (brand.fullVersion || "")
                + "\n规格：" + (brand.versionSpec || "年份.季度.buildId.commitId")
                + "\n\n支持 Fabric / Forge / NeoForge / LabyMod / Modrinth / 正版登录。"
        }

        Text {
            color: SpectrumTheme.primary
            font.pixelSize: 13
            text: "github.com/" + (brand.githubRepo || "HPLAY-dev/spectrum-minecraft-launcher")
            font.underline: true
        }
    }
}
