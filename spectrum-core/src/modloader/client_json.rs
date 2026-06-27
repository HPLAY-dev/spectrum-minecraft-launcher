//! Forge / NeoForge 客户端 JSON 安装（PyO3 与 Python download_*_json 对齐）

use super::forge::ForgeInstaller;
use super::neoforge::NeoForgeInstaller;
use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::manifest::{ManifestManager, VersionJsonManager};
use crate::types::*;
use std::path::Path;

const BMCLAPI_FORGE: &str = "https://bmclapi2.bangbang93.com/forge/minecraft";
const BMCLAPI_NEOFORGE: &str = "https://bmclapi2.bangbang93.com/neoforge/list";

async fn resolve_forge_loader_version(
    client: &HttpClient,
    mc_version: &str,
    forge_version: Option<&str>,
) -> CoreResult<String> {
    if let Some(v) = forge_version.filter(|s| !s.is_empty() && *s != "latest") {
        return Ok(v.to_string());
    }
    let url = format!("{}/{}", BMCLAPI_FORGE, mc_version);
    let resolved = client.resolve_url(&url);
    let list: Vec<serde_json::Value> = client.get_json(&resolved).await?;
    list.first()
        .and_then(|e| e["version"].as_str().map(String::from))
        .ok_or_else(|| CoreError::Installer(format!("Forge 无可用版本: {mc_version}")))
}

async fn resolve_neoforge_loader_version(
    client: &HttpClient,
    mc_version: &str,
    neoforge_version: Option<&str>,
) -> CoreResult<String> {
    if let Some(v) = neoforge_version.filter(|s| !s.is_empty() && *s != "latest") {
        return Ok(v.to_string());
    }
    let url = format!("{}/{}", BMCLAPI_NEOFORGE, mc_version);
    let resolved = client.resolve_url(&url);
    let list: Vec<serde_json::Value> = client.get_json(&resolved).await?;
    list.last()
        .and_then(|e| e["version"].as_str().map(String::from))
        .ok_or_else(|| CoreError::Installer(format!("NeoForge 无可用版本: {mc_version}")))
}

pub async fn download_forge_json(
    client: HttpClient,
    minecraft_dir: &Path,
    mc_version: &str,
    instance_name: &str,
    forge_version: Option<&str>,
    _bmclapi: bool,
    _java: &str,
) -> CoreResult<()> {
    let lv = resolve_forge_loader_version(&client, mc_version, forge_version).await?;
    let instance_dir = minecraft_dir.join("versions").join(instance_name);
    tokio::fs::create_dir_all(&instance_dir).await?;

    let installer = ForgeInstaller::new(client.clone());
    let forge_vj = ModLoaderInstaller::install(
        &installer,
        mc_version,
        Some(&lv),
        &instance_dir,
        minecraft_dir,
    )
    .await?;

    let mut manifest = ManifestManager::new(client.clone());
    let mut vjm = VersionJsonManager::new(client);
    let json_path = instance_dir.join(format!("{instance_name}.json"));
    super::instance_json::merge_and_save_instance_json(
        &mut vjm,
        &mut manifest,
        forge_vj,
        mc_version,
        instance_name,
        &json_path,
    )
    .await?;
    Ok(())
}

pub async fn download_neoforge_json(
    client: HttpClient,
    minecraft_dir: &Path,
    mc_version: &str,
    instance_name: &str,
    neoforge_version: Option<&str>,
    _bmclapi: bool,
    _java: &str,
) -> CoreResult<()> {
    let lv = resolve_neoforge_loader_version(&client, mc_version, neoforge_version).await?;
    let instance_dir = minecraft_dir.join("versions").join(instance_name);
    tokio::fs::create_dir_all(&instance_dir).await?;

    let installer = NeoForgeInstaller::new(client.clone());
    let neo_vj = ModLoaderInstaller::install(
        &installer,
        mc_version,
        Some(&lv),
        &instance_dir,
        minecraft_dir,
    )
    .await?;

    let mut manifest = ManifestManager::new(client.clone());
    let mut vjm = VersionJsonManager::new(client);
    let json_path = instance_dir.join(format!("{instance_name}.json"));
    super::instance_json::merge_and_save_instance_json(
        &mut vjm,
        &mut manifest,
        neo_vj,
        mc_version,
        instance_name,
        &json_path,
    )
    .await?;
    Ok(())
}

/// BMCLAPI Forge 版本列表（与 Python get_forge_version 返回结构一致）
pub async fn get_forge_version_list(
    client: &HttpClient,
    mc_version: &str,
) -> CoreResult<Vec<serde_json::Value>> {
    let url = format!("{}/{}", BMCLAPI_FORGE, mc_version);
    let resolved = client.resolve_url(&url);
    client.get_json(&resolved).await
}

/// BMCLAPI NeoForge 版本列表
pub async fn get_neoforge_version_list(
    client: &HttpClient,
    mc_version: &str,
) -> CoreResult<Vec<serde_json::Value>> {
    let url = format!("{}/{}", BMCLAPI_NEOFORGE, mc_version);
    let resolved = client.resolve_url(&url);
    client.get_json(&resolved).await
}
