//! # NeoForge ModLoader 安装器
//!
//! 下载 installer.jar 并执行 `--installClient` 生成 patched client 与完整库。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::Stdio;

const NEOFORGE_MAVEN: &str = "https://maven.neoforged.net/releases";
const BMCLAPI_NEOFORGE: &str = "https://bmclapi2.bangbang93.com/neoforge/list";

const LAUNCHER_PROFILES_STUB: &str = r#"{
  "profiles": {},
  "selectedProfile": "",
  "clientToken": "00000000000000000000000000000000",
  "authenticationDatabase": {},
  "launcherVersion": { "name": "SerenaLauncher", "format": 21 }
}"#;

pub struct NeoForgeInstaller {
    client: HttpClient,
}

impl NeoForgeInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    fn installer_path(minecraft_dir: &Path, loader_version: &str) -> PathBuf {
        minecraft_dir
            .join("cache")
            .join("installers")
            .join(format!("neoforge-{loader_version}-installer.jar"))
    }

    fn generated_json_path(minecraft_dir: &Path, loader_version: &str) -> PathBuf {
        minecraft_dir
            .join("versions")
            .join(format!("neoforge-{loader_version}"))
            .join(format!("neoforge-{loader_version}.json"))
    }

    async fn ensure_launcher_profiles(minecraft_dir: &Path) -> CoreResult<()> {
        let path = minecraft_dir.join("launcher_profiles.json");
        if path.exists() {
            return Ok(());
        }
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        tokio::fs::write(&path, LAUNCHER_PROFILES_STUB).await?;
        Ok(())
    }

    async fn download_installer(
        &self,
        loader_version: &str,
        minecraft_dir: &Path,
    ) -> CoreResult<PathBuf> {
        let installer_path = Self::installer_path(minecraft_dir, loader_version);
        if installer_path.exists() {
            return Ok(installer_path);
        }

        let installer_url = format!(
            "{NEOFORGE_MAVEN}/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar"
        );
        let resolved_url = self.client.resolve_url(&installer_url);

        if let Some(parent) = installer_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        log::info!("下载 NeoForge 安装器: {loader_version}");
        self.client
            .download_file(&resolved_url, &installer_path, None::<fn(u64, u64)>)
            .await?;
        Ok(installer_path)
    }

    async fn run_install_client(
        installer_path: &Path,
        minecraft_dir: &Path,
    ) -> CoreResult<()> {
        Self::ensure_launcher_profiles(minecraft_dir).await?;

        log::info!("运行 NeoForge 安装器（处理 client 与库）…");
        let status = tokio::process::Command::new("java")
            .arg("-jar")
            .arg(installer_path)
            .arg("--installClient")
            .arg(minecraft_dir)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .status()
            .await
            .map_err(|e| CoreError::Installer(format!("无法启动 NeoForge 安装器: {e}")))?;

        if !status.success() {
            return Err(CoreError::Installer(
                "NeoForge 安装器执行失败，请检查网络或 Java 环境".into(),
            ));
        }
        Ok(())
    }

    async fn load_generated_version_json(
        minecraft_dir: &Path,
        loader_version: &str,
    ) -> CoreResult<VersionJson> {
        let json_path = Self::generated_json_path(minecraft_dir, loader_version);
        let content = tokio::fs::read_to_string(&json_path).await.map_err(|_| {
            CoreError::Installer(format!(
                "NeoForge 安装后未找到 {json_path}",
                json_path = json_path.display()
            ))
        })?;
        serde_json::from_str(&content).map_err(CoreError::Json)
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

        let client_jar = super::instance_json::neoforge_client_jar_path(minecraft_dir, &lv);
        let installer_path = self.download_installer(&lv, minecraft_dir).await?;

        if !client_jar.exists() {
            Self::run_install_client(&installer_path, minecraft_dir).await?;
        }

        let vj = Self::load_generated_version_json(minecraft_dir, &lv)
            .await
            .or_else(|_| Self::extract_version_from_installer(&installer_path, &lv))?;

        let sidecar_path = instance_dir.join(format!("{}.json", vj.id));
        let content = serde_json::to_string_pretty(&vj)?;
        tokio::fs::write(&sidecar_path, content).await?;

        log::info!("NeoForge {lv} 安装完成 (MC {mc_version})");
        Ok(vj)
    }
}
