//! # Fabric ModLoader 安装器
//!
//! 从 Fabric Maven 获取元数据并生成版本 JSON。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use std::path::Path;

/// Fabric Meta API 端点
const FABRIC_META_API: &str = "https://meta.fabricmc.net/v2";

pub struct FabricInstaller {
    client: HttpClient,
}

impl FabricInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }
}

#[async_trait]
impl ModLoaderInstaller for FabricInstaller {
    fn name(&self) -> &'static str {
        "Fabric"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        let url = format!("{}/versions/game", FABRIC_META_API);
        let resolved = self.client.resolve_url(&url);
        let versions: Vec<serde_json::Value> = self.client.get_json(&resolved).await?;
        Ok(versions.iter()
            .filter_map(|v| v["version"].as_str().map(String::from))
            .collect())
    }

    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>> {
        let url = format!("{}/versions/loader/{}", FABRIC_META_API, mc_version);
        let resolved = self.client.resolve_url(&url);
        let versions: Vec<serde_json::Value> = self.client.get_json(&resolved).await?;
        Ok(versions.iter()
            .filter_map(|v| v["loader"]["version"].as_str().map(String::from))
            .collect())
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
                        format!("Fabric 不支持 Minecraft {}", mc_version)
                    ))?
            }
        };

        // 从 Fabric Meta API 获取合并后的 version json
        let url = format!(
            "{}/versions/loader/{}/{}/profile/json",
            FABRIC_META_API, mc_version, lv
        );
        let resolved = self.client.resolve_url(&url);

        log::info!("下载 Fabric 版本 JSON: {}", resolved);
        let mut fabric_vj: VersionJson = self.client.get_json(&resolved).await?;

        // 设置正确的 ID
        fabric_vj.id = format!("fabric-{}-{}", mc_version, lv);

        // 保存 version json
        let json_path = instance_dir.join(format!("{}.json", fabric_vj.id));
        tokio::fs::create_dir_all(instance_dir).await?;
        let content = serde_json::to_string_pretty(&fabric_vj)?;
        tokio::fs::write(&json_path, content).await?;

        log::info!("Fabric {} 安装完成", lv);
        Ok(fabric_vj)
    }
}
