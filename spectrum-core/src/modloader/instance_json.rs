//! 实例 version.json 检测、合并与修复

use crate::manifest::{ManifestManager, VersionJsonManager};
use crate::modloader::json_merge;
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

/// 从实例名猜测 ModLoader（如 `1.21.1nf` → NeoForge）
pub fn guess_modloader_from_name(instance_name: &str) -> Option<ModLoader> {
    let n = instance_name.to_lowercase();
    if n.contains("neoforge") || n.ends_with("nf") {
        return Some(ModLoader::NeoForge);
    }
    if n.contains("fabric") {
        return Some(ModLoader::Fabric);
    }
    if n.contains("forge") {
        return Some(ModLoader::Forge);
    }
    None
}

/// 从实例名或 JSON 推断 Minecraft 基版本
pub fn guess_mc_version(instance_name: &str, vj: &VersionJson) -> String {
    if let Some(parent) = vj.inherits_from.as_ref().filter(|s| !s.is_empty()) {
        return parent.clone();
    }
    let id = vj.id.trim();
    if !id.is_empty() && id.chars().next().is_some_and(|c| c.is_ascii_digit()) {
        return id.to_string();
    }
    for part in instance_name.split(|c: char| !c.is_ascii_digit() && c != '.') {
        if part.matches('.').count() >= 1 && part.chars().next().is_some_and(|c| c.is_ascii_digit()) {
            return part.to_string();
        }
    }
    VersionJsonManager::get_minecraft_version(vj)
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
    let mut merged = json_merge::merge_version_json(&loader_vj, &vanilla_vj)?;
    merged.id = instance_name.to_string();
    merged.inherits_from = None;
    vjm.save_to_file(&merged, json_path).await?;
    Ok(merged)
}
