//! # LabyMod 安装器
//!
//! LabyMod 使用自己的 API 获取版本信息并注入。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use std::path::Path;

/// LabyMod API 端点
const LABYMOD_API: &str = "https://api.labymod.net/v2";
const LABYMOD_DOWNLOAD: &str = "https://download.labymod.net";

pub struct LabyModInstaller {
    client: HttpClient,
}

impl LabyModInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }
}

#[async_trait]
impl ModLoaderInstaller for LabyModInstaller {
    fn name(&self) -> &'static str {
        "LabyMod"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        let url = format!("{}/meta/versions", LABYMOD_API);
        let resolved = self.client.resolve_url(&url);
        let data: serde_json::Value = self.client.get_json(&resolved).await?;

        let mut versions: Vec<String> = Vec::new();
        if let Some(arr) = data.as_array() {
            for entry in arr {
                if let Some(mc_version) = entry["minecraftVersion"].as_str() {
                    versions.push(mc_version.to_string());
                }
            }
        }

        versions.sort();
        versions.dedup();
        Ok(versions)
    }

    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>> {
        let url = format!("{}/meta/versions", LABYMOD_API);
        let resolved = self.client.resolve_url(&url);
        let data: serde_json::Value = self.client.get_json(&resolved).await?;

        let mut versions: Vec<String> = Vec::new();
        if let Some(arr) = data.as_array() {
            for entry in arr {
                if entry["minecraftVersion"].as_str() == Some(mc_version) {
                    if let Some(lm_version) = entry["labymodVersion"].as_str() {
                        versions.push(lm_version.to_string());
                    }
                }
            }
        }

        versions.sort();
        versions.reverse();
        Ok(versions)
    }

    async fn install(
        &self,
        mc_version: &str,
        loader_version: Option<&str>,
        instance_dir: &Path,
        _minecraft_dir: &Path,
    ) -> CoreResult<VersionJson> {
        let lv = match loader_version {
            Some(v) => v.to_string(),
            None => {
                let versions = self.get_loader_versions(mc_version).await?;
                versions.first().cloned()
                    .ok_or_else(|| CoreError::Installer(
                        format!("LabyMod 不支持 Minecraft {}", mc_version)
                    ))?
            }
        };

        // 下载 LabyMod JAR
        let download_url = format!("{}/labymod_{}_{}.jar", LABYMOD_DOWNLOAD, mc_version, lv);
        let resolved = self.client.resolve_url(&download_url);

        let jar_path = instance_dir.join(format!("LabyMod-{}-{}.jar", mc_version, lv));
        tokio::fs::create_dir_all(instance_dir).await?;

        log::info!("下载 LabyMod: {} {}", mc_version, lv);
        self.client.download_file(&resolved, &jar_path, None::<fn(u64, u64)>).await?;

        // 构建 version.json (LabyMod 通过继承原版工作)
        let vj = VersionJson {
            id: format!("labymod-{}-{}", mc_version, lv),
            main_class: "net.minecraft.launchwrapper.Launch".into(),
            inherits_from: Some(mc_version.to_string()),
            minecraft_arguments: Some(
                "--username ${auth_player_name} --version ${version_name} \
                 --gameDir ${game_directory} --assetsDir ${game_assets} \
                 --assetIndex ${assets_index_name} --uuid ${auth_uuid} \
                 --accessToken ${auth_access_token} --userType ${user_type} \
                 --versionType ${version_type}"
                    .into()
            ),
            libraries: vec![
                Library {
                    name: format!("labymod:labymod:{}:{}", mc_version, lv),
                    url: Some("file:///".into()),
                    downloads: None,
                    rules: None,
                    natives: None,
                    extract: None,
                },
            ],
            ..Default::default()
        };

        let json_path = instance_dir.join(format!("{}.json", &vj.id));
        let content = serde_json::to_string_pretty(&vj)?;
        tokio::fs::write(&json_path, content).await?;

        log::info!("LabyMod {} {} 安装完成", mc_version, lv);
        Ok(vj)
    }
}
