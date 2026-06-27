//! 实例 version.json 检测、合并与修复

use crate::manifest::{ManifestManager, VersionJsonManager};
use crate::types::*;
use std::path::Path;

/// 从 version.json 内容推断 ModLoader
pub fn detect_modloader_in_json(vj: &VersionJson) -> ModLoader {
    let main_class = vj.main_class.to_lowercase();
    let libs_concat: String = vj
        .libraries
        .iter()
        .map(|l| l.name.to_lowercase())
        .collect::<Vec<_>>()
        .join(" ");

    if main_class.contains("knotclient") || libs_concat.contains("fabric-loader") {
        ModLoader::Fabric
    } else if libs_concat.contains("net.neoforged") || main_class.contains("bootstraplauncher") {
        ModLoader::NeoForge
    } else if libs_concat.contains("net.minecraftforge") || main_class.contains("modlauncher") {
        ModLoader::Forge
    } else if libs_concat.contains("optifine") {
        ModLoader::OptiFine
    } else if libs_concat.contains("labymod") {
        ModLoader::LabyMod
    } else {
        ModLoader::Vanilla
    }
}

/// 是否为原版启动配置（无 ModLoader）
pub fn is_vanilla_launch_profile(vj: &VersionJson) -> bool {
    detect_modloader_in_json(vj) == ModLoader::Vanilla
        && vj.main_class.contains("net.minecraft.client.main.Main")
}

/// 从实例名或 JSON 推断 ModLoader（JSON 优先，否则解析实例名）
pub fn detect_modloader(instance_name: &str, vj: &VersionJson) -> ModLoader {
    let from_json = detect_modloader_in_json(vj);
    if from_json != ModLoader::Vanilla {
        return from_json;
    }
    guess_modloader_from_name(instance_name).unwrap_or(ModLoader::Vanilla)
}

/// 实例版本摘要（MC 基版本 + ModLoader + Loader 版本号）
#[derive(Debug, Clone)]
pub struct InstanceVersionInfo {
    pub mc_version: String,
    pub modloader: ModLoader,
    pub loader_version: Option<String>,
}

pub fn resolve_instance_version(
    instance_name: &str,
    vj: &VersionJson,
    instance_dir: Option<&Path>,
) -> InstanceVersionInfo {
    InstanceVersionInfo {
        mc_version: guess_mc_version_in_dir(instance_name, vj, instance_dir),
        modloader: detect_modloader(instance_name, vj),
        loader_version: loader_version_from_json(vj),
    }
}

/// 从实例名猜测 ModLoader（如 `1.21.1nf` → NeoForge）
pub fn guess_modloader_from_name(instance_name: &str) -> Option<ModLoader> {
    let n = instance_name.to_lowercase();
    if n.contains("neoforge") || re_suffix_nf(&n) {
        return Some(ModLoader::NeoForge);
    }
    if n.contains("fabric") {
        return Some(ModLoader::Fabric);
    }
    if n.contains("forge") && !n.contains("neoforge") {
        return Some(ModLoader::Forge);
    }
    None
}

/// `1.21.1nf` / `1.20.4-fabric` 等实例名后缀
fn re_suffix_nf(n: &str) -> bool {
    n.ends_with("nf")
        && n.len() > 2
        && n.as_bytes().get(n.len() - 3).copied().unwrap_or(b'0').is_ascii_digit()
}

/// 从实例名或 JSON 推断 Minecraft 基版本
pub fn guess_mc_version(instance_name: &str, vj: &VersionJson) -> String {
    guess_mc_version_in_dir(instance_name, vj, None)
}

/// 优先读 client.jar 内嵌 version.json，其次 JSON / 实例名
pub fn guess_mc_version_in_dir(
    instance_name: &str,
    vj: &VersionJson,
    instance_dir: Option<&Path>,
) -> String {
    if let Some(dir) = instance_dir {
        if let Some(mc) =
            crate::client_jar::read_mc_version_from_instance(dir, instance_name, &vj.id)
        {
            return mc;
        }
    }
    if let Some(mc) = fml_mc_version_from_json(vj) {
        return mc;
    }
    if let Some(parent) = vj.inherits_from.as_ref().filter(|s| !s.is_empty()) {
        return parent.clone();
    }
    // version.json 的 id 是官方版本号（如 b1.0、1.0、1.21.1nf），优先于实例文件夹名
    let from_json = normalize_mc_version(&vj.id);
    if !from_json.is_empty() {
        return from_json;
    }
    normalize_mc_version(instance_name)
}

/// ModLoader JSON 缺少原版元数据（assetIndex / downloads 等）
pub fn needs_vanilla_metadata(vj: &VersionJson) -> bool {
    detect_modloader_in_json(vj) != ModLoader::Vanilla
        && (vj.asset_index.is_none() || vj.downloads.is_none() || vj.java_version.is_none())
}

/// 从 JSON 推断 MC 基版本（无实例目录时无法读 jar）
pub fn guess_mc_version_from_json(vj: &VersionJson) -> String {
    if let Some(mc) = fml_mc_version_from_json(vj) {
        return mc;
    }
    if let Some(parent) = vj.inherits_from.as_ref().filter(|s| !s.is_empty()) {
        return parent.clone();
    }
    normalize_mc_version(&vj.id)
}

/// 从 game 参数读取 Minecraft 基版本
pub fn fml_mc_version_from_json(vj: &VersionJson) -> Option<String> {
    let args = vj.arguments.as_ref()?;
    let flat: Vec<String> = args
        .game
        .iter()
        .flat_map(|a| match a {
            Argument::Value(s) => vec![s.clone()],
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => vec![s.clone()],
                ArgumentValue::Multi(v) => v.clone(),
            },
        })
        .collect();
    for i in 0..flat.len().saturating_sub(1) {
        if flat[i] == "--fml.mcVersion" {
            return Some(flat[i + 1].clone());
        }
    }
    None
}

/// 从实例 id / 版本 id 提取 Minecraft 基版本（如 `1.21.1nf` → `1.21.1`）
pub fn normalize_mc_version(raw: &str) -> String {
    let v = raw.trim().split(['-', '+']).next().unwrap_or(raw.trim());
    let v = strip_modloader_version_suffix(v);
    let parts: Vec<&str> = v.split('.').collect();
    if parts.first() == Some(&"1") && parts.len() >= 2 {
        if let Ok(minor) = parts[1].parse::<u32>() {
            if parts.len() >= 3 {
                let patch: String = parts[2].chars().take_while(|c| c.is_ascii_digit()).collect();
                if let Ok(patch_num) = patch.parse::<u32>() {
                    return format!("1.{minor}.{patch_num}");
                }
            }
            return format!("1.{minor}");
        }
    }
    v.to_string()
}

fn strip_modloader_version_suffix(v: &str) -> &str {
    let lower = v.to_ascii_lowercase();
    for suffix in ["neoforge", "fabric", "forge", "optifine", "nf"] {
        if lower.ends_with(suffix) && v.len() > suffix.len() {
            let base = &v[..v.len() - suffix.len()];
            if base.chars().last().is_some_and(|c| c.is_ascii_digit()) {
                return base;
            }
        }
    }
    v
}

/// ModLoader 安装器版本（NeoForge 21.1.234、Fabric loader 等）
pub fn loader_version_from_json(vj: &VersionJson) -> Option<String> {
    if let Some(v) = neoforge_version_from_json(vj) {
        return Some(v);
    }
    if let Some(v) = forge_version_from_json(vj) {
        return Some(v);
    }
    fabric_loader_version_from_json(vj)
}

pub fn forge_version_from_json(vj: &VersionJson) -> Option<String> {
    let args = vj.arguments.as_ref()?;
    let flat: Vec<String> = args
        .game
        .iter()
        .flat_map(|a| match a {
            Argument::Value(s) => vec![s.clone()],
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => vec![s.clone()],
                ArgumentValue::Multi(v) => v.clone(),
            },
        })
        .collect();
    for i in 0..flat.len().saturating_sub(1) {
        if flat[i] == "--fml.forgeVersion" || flat[i] == "--forgeVersion" {
            return Some(flat[i + 1].clone());
        }
    }
    None
}

fn fabric_loader_version_from_json(vj: &VersionJson) -> Option<String> {
    for lib in &vj.libraries {
        if let Some(rest) = lib.name.strip_prefix("net.fabricmc:fabric-loader:") {
            return Some(rest.to_string());
        }
    }
    None
}

/// 从 game 参数读取 NeoForge 版本号
pub fn neoforge_version_from_json(vj: &VersionJson) -> Option<String> {
    let args = vj.arguments.as_ref()?;
    let flat: Vec<String> = args
        .game
        .iter()
        .flat_map(|a| match a {
            Argument::Value(s) => vec![s.clone()],
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => vec![s.clone()],
                ArgumentValue::Multi(v) => v.clone(),
            },
        })
        .collect();
    for i in 0..flat.len().saturating_sub(1) {
        if flat[i] == "--fml.neoForgeVersion" {
            return Some(flat[i + 1].clone());
        }
    }
    None
}

/// 从 game 参数读取 NeoForm 版本号
pub fn neoform_version_from_json(vj: &VersionJson) -> Option<String> {
    let args = vj.arguments.as_ref()?;
    let flat: Vec<String> = args
        .game
        .iter()
        .flat_map(|a| match a {
            Argument::Value(s) => vec![s.clone()],
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => vec![s.clone()],
                ArgumentValue::Multi(v) => v.clone(),
            },
        })
        .collect();
    for i in 0..flat.len().saturating_sub(1) {
        if flat[i] == "--fml.neoFormVersion" {
            return Some(flat[i + 1].clone());
        }
    }
    None
}

pub fn neoforge_client_jar_path(minecraft_dir: &Path, loader_version: &str) -> std::path::PathBuf {
    minecraft_dir.join(format!(
        "libraries/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-client.jar"
    ))
}

pub fn neoforge_install_incomplete(minecraft_dir: &Path, vj: &VersionJson) -> bool {
    if detect_modloader_in_json(vj) != ModLoader::NeoForge {
        return false;
    }
    if needs_vanilla_metadata(vj) {
        return true;
    }
    if let Some(ver) = neoforge_version_from_json(vj) {
        return !neoforge_client_jar_path(minecraft_dir, &ver).exists();
    }
    true
}

/// 合并 ModLoader + 原版 JSON 并写入实例文件
pub async fn merge_and_save_instance_json(
    vjm: &mut VersionJsonManager,
    manifest: &mut ManifestManager,
    loader_vj: VersionJson,
    mc_version: &str,
    instance_name: &str,
    json_path: &Path,
) -> CoreResult<VersionJson> {
    let vanilla_vj = vjm.get_version_json(mc_version, manifest).await?;
    let mut merged = VersionJsonManager::merge_version_json(loader_vj, vanilla_vj)?;
    merged.id = instance_name.to_string();
    merged.inherits_from = None;
    vjm.save_to_file(&merged, json_path).await?;
    Ok(merged)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalize_strips_neoforge_suffix() {
        assert_eq!(normalize_mc_version("1.21.1nf"), "1.21.1");
        assert_eq!(normalize_mc_version("1.20.4-fabric"), "1.20.4");
        assert_eq!(normalize_mc_version("1.21.1"), "1.21.1");
    }

    #[test]
    fn guess_modloader_from_instance_name() {
        assert_eq!(
            guess_modloader_from_name("1.21.1nf"),
            Some(ModLoader::NeoForge)
        );
        assert_eq!(guess_modloader_from_name("1.21.1"), None);
    }

    #[test]
    fn guess_mc_version_prefers_json_id_over_folder_name() {
        let vj: VersionJson = serde_json::from_str(r#"{"id":"b1.0","mainClass":"x","libraries":[]}"#)
            .unwrap();
        assert_eq!(guess_mc_version_in_dir("test3", &vj, None), "b1.0");

        let vj2: VersionJson = serde_json::from_str(r#"{"id":"1.0","mainClass":"x","libraries":[]}"#)
            .unwrap();
        assert_eq!(guess_mc_version_in_dir("test5", &vj2, None), "1.0");
    }
}
