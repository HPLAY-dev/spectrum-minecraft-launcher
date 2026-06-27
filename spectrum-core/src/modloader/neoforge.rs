//! # NeoForge ModLoader 安装器
//!
//! NeoForge 1.20.1+ 使用 `net.neoforged:neoforge` 与 installer.jar 内的 version.json。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use std::io::Read;
use std::path::Path;

const NEOFORGE_MAVEN: &str = "https://maven.neoforged.net/releases";
const BMCLAPI_NEOFORGE: &str = "https://bmclapi2.bangbang93.com/neoforge/list";

pub struct NeoForgeInstaller {
    client: HttpClient,
}

impl NeoForgeInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    fn extract_version_from_installer(installer_path: &Path, neo_version: &str) -> CoreResult<VersionJson> {
        let file = std::fs::File::open(installer_path)?;
        let mut archive = zip::ZipArchive::new(file)?;

        for path in ["version.json"] {
            if let Ok(mut file) = archive.by_name(path) {
                let mut content = String::new();
                file.read_to_string(&mut content)?;
                let mut vj: VersionJson = serde_json::from_str(&content)?;
                vj.id = format!("neoforge-{neo_version}");
                return Ok(vj);
            }
        }

        Err(CoreError::Installer(
            "未在 NeoForge 安装器中找到 version.json".into(),
        ))
    }
}

#[async_trait]
impl ModLoaderInstaller for NeoForgeInstaller {
    fn name(&self) -> &'static str {
        "NeoForge"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        Ok(vec![])
    }

    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>> {
        let url = format!("{BMCLAPI_NEOFORGE}/{mc_version}");
        let resolved = self.client.resolve_url(&url);
        let list: Vec<serde_json::Value> = self.client.get_json(&resolved).await?;
        let mut versions: Vec<String> = list
            .iter()
            .filter_map(|e| e["version"].as_str().map(String::from))
            .collect();
        versions.reverse();
        Ok(versions)
    }

    async fn install(
        &self,
        mc_version: &str,
        loader_version: Option<&str>,
        instance_dir: &Path,
        minecraft_dir: &Path,
    ) -> CoreResult<VersionJson> {
        let lv = match loader_version {
            Some(v) => v.to_string(),
            None => {
                let versions = self.get_loader_versions(mc_version).await?;
                versions.first().cloned().ok_or_else(|| {
                    CoreError::Installer(format!("NeoForge 不支持 Minecraft {mc_version}"))
                })?
            }
        };

        let installer_url = format!(
            "{NEOFORGE_MAVEN}/net/neoforged/neoforge/{lv}/neoforge-{lv}-installer.jar"
        );
        let resolved_url = self.client.resolve_url(&installer_url);

        let installer_dir = minecraft_dir.join("cache").join("installers");
        tokio::fs::create_dir_all(&installer_dir).await?;
        let installer_path = installer_dir.join(format!("neoforge-{lv}-installer.jar"));

        if !installer_path.exists() {
            log::info!("下载 NeoForge 安装器: {lv}");
            self.client
                .download_file(&resolved_url, &installer_path, None::<fn(u64, u64)>)
                .await?;
        }

        let vj = Self::extract_version_from_installer(&installer_path, &lv)?;

        let json_path = instance_dir.join(format!("{}.json", vj.id));
        tokio::fs::create_dir_all(instance_dir).await?;
        let content = serde_json::to_string_pretty(&vj)?;
        tokio::fs::write(&json_path, content).await?;

        log::info!("NeoForge {lv} 安装完成 (MC {mc_version})");
        Ok(vj)
    }
}
