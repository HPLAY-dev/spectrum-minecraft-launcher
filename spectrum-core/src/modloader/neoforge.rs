//! # NeoForge ModLoader 安装器
//!
//! NeoForge (原 Forge 的社区分支, 1.20.1+)。
//! 使用 NeoForge Maven 仓库获取元数据。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use quick_xml::Reader;
use quick_xml::events::Event;
use std::path::Path;

/// NeoForge Maven 仓库
const NEOFORGE_MAVEN: &str = "https://maven.neoforged.net/releases";

pub struct NeoForgeInstaller {
    client: HttpClient,
}

impl NeoForgeInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    /// 解析 Maven Metadata XML
    async fn fetch_maven_metadata(&self, artifact_path: &str) -> CoreResult<Vec<String>> {
        let url = format!("{}/{}/maven-metadata.xml", NEOFORGE_MAVEN, artifact_path);
        let resolved = self.client.resolve_url(&url);
        let xml = self.client.get_text(&resolved).await?;

        let mut reader = Reader::from_str(&xml);
        let mut buf = Vec::new();
        let mut in_versions = false;
        let mut versions = Vec::new();
        let mut current_text = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    if e.name().as_ref() == b"versions" {
                        in_versions = true;
                    }
                }
                Ok(Event::Text(ref e)) => {
                    current_text = e.unescape().unwrap_or_default().to_string();
                }
                Ok(Event::End(ref e)) => {
                    if e.name().as_ref() == b"version" && in_versions {
                        versions.push(current_text.clone());
                    }
                    if e.name().as_ref() == b"versions" {
                        break;
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(CoreError::Xml(format!("XML 解析错误: {}", e))),
                _ => {}
            }
            buf.clear();
        }

        versions.reverse();
        Ok(versions)
    }
}

#[async_trait]
impl ModLoaderInstaller for NeoForgeInstaller {
    fn name(&self) -> &'static str {
        "NeoForge"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        let versions = self.fetch_maven_metadata("net/neoforged/forge").await?;
        let mut mc_versions: Vec<String> = versions.iter()
            .filter_map(|v| {
                let dash_pos = v.find('-')?;
                Some(v[..dash_pos].to_string())
            })
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect();
        mc_versions.sort();
        Ok(mc_versions)
    }

    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>> {
        let all_versions = self.fetch_maven_metadata("net/neoforged/forge").await?;
        let prefix = format!("{}-", mc_version);
        let mut versions: Vec<String> = all_versions.iter()
            .filter(|v| v.starts_with(&prefix))
            .map(|v| v[prefix.len()..].to_string())
            .collect();
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
                        format!("NeoForge 不支持 Minecraft {}", mc_version)
                    ))?
            }
        };

        let neo_version = format!("{}-{}", mc_version, lv);

        // 下载 NeoForge 的 version.json (NeoForge 使用类似 Fabric 的 profile JSON)
        let profile_url = format!(
            "{}/net/neoforged/forge/{}/forge-{}-profile.json",
            NEOFORGE_MAVEN, neo_version, neo_version
        );
        let resolved = self.client.resolve_url(&profile_url);

        log::info!("下载 NeoForge profile JSON: {}", resolved);
        let neo_vj: VersionJson = match self.client.get_json(&resolved).await {
            Ok(vj) => vj,
            Err(_) => {
                // 回退: 尝试下载安装器 JSON
                let installer_json_url = format!(
                    "{}/net/neoforged/forge/{}/forge-{}-installer.json",
                    NEOFORGE_MAVEN, neo_version, neo_version
                );
                let resolved_ij = self.client.resolve_url(&installer_json_url);
                self.client.get_json(&resolved_ij).await?
            }
        };

        // 保存
        let vj_id = format!("neoforge-{}", neo_version);
        let mut result_vj = neo_vj;
        result_vj.id = vj_id.clone();

        let json_path = instance_dir.join(format!("{}.json", vj_id));
        tokio::fs::create_dir_all(instance_dir).await?;
        let content = serde_json::to_string_pretty(&result_vj)?;
        tokio::fs::write(&json_path, content).await?;

        log::info!("NeoForge {} 安装完成", neo_version);
        Ok(result_vj)
    }
}
