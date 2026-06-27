//! # OptiFine 安装器
//!
//! OptiFine 的安装比较特殊:
//! 1. 从 OptiFine 官网获取版本列表
//! 2. 下载 OptiFine JAR (实际是一个 ZIP)
//! 3. 从 JAR 中提取版本 JSON 和 Patch JAR
//! 4. 合并到原版 version.json

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use regex::Regex;
use std::path::Path;

/// OptiFine 下载页面
const OPTIFINE_HOME: &str = "https://optifine.net";
const OPTIFINE_DOWNLOAD_BASE: &str = "https://optifine.net/downloads";

pub struct OptiFineInstaller {
    client: HttpClient,
}

impl OptiFineInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    /// 解析下载页面, 获取所有版本的下载链接
    async fn parse_download_page(&self) -> CoreResult<Vec<(String, String)>> {
        // 获取 OptiFine 版本列表页面
        let html = self.client.get_text(OPTIFINE_HOME).await?;

        // 匹配下载链接: /downloads/xxx
        let re = Regex::new(r#"href="/downloads/([^"]+)"#)
            .map_err(|e| CoreError::Xml(format!("无法编译正则: {e}")))?;

        let mut versions: Vec<(String, String)> = Vec::new();

        for cap in re.captures_iter(&html) {
            if let Some(href) = cap.get(1) {
                let version_id = href.as_str().to_string();
                // 构造版本名: 从 ID 提取
                let name = version_id
                    .replace("HD_U_", "HD U ")
                    .replace("HD_M_", "HD M ")
                    .replace("_", " ");
                versions.push((name, version_id));
            }
        }

        // 去重并排序
        versions.sort_by(|a, b| b.1.cmp(&a.1));
        versions.dedup_by(|a, b| a.1 == b.1);

        Ok(versions)
    }

    /// 提取 OptiFine 版本对应的 Minecraft 版本
    fn extract_mc_version(optifine_version: &str) -> Option<String> {
        // OptiFine HD U G6 预发布版 1.20.4 → 1.20.4
        // 文件名: optifine_1.20.4_HD_U_G6.jar
        let re = Regex::new(r"(\d+\.\d+(?:\.\d+)?)").ok()?;
        re.captures(optifine_version)?
            .get(1)
            .map(|m| m.as_str().to_string())
    }
}

#[async_trait]
impl ModLoaderInstaller for OptiFineInstaller {
    fn name(&self) -> &'static str {
        "OptiFine"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        let entries = self.parse_download_page().await?;
        let mut mc_versions: Vec<String> = entries.iter()
            .filter_map(|(_, id)| Self::extract_mc_version(id))
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect();
        mc_versions.sort();
        Ok(mc_versions)
    }

    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>> {
        let entries = self.parse_download_page().await?;
        let mut versions: Vec<String> = entries.iter()
            .filter(|(_, id)| id.contains(mc_version))
            .map(|(name, _)| name.clone())
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
        let entries = self.parse_download_page().await?;

        // 找到匹配的版本
        let (optifine_name, optifine_id) = match loader_version {
            Some(name) => {
                entries.into_iter().find(|(n, _)| n == name)
                    .ok_or_else(|| CoreError::Installer(format!("未找到 OptiFine 版本: {}", name)))?
            }
            None => {
                entries.into_iter()
                    .filter(|(_, id)| id.contains(mc_version))
                    .next()
                    .ok_or_else(|| CoreError::Installer(
                        format!("OptiFine 不支持 Minecraft {}", mc_version)
                    ))?
            }
        };

        // 下载 OptiFine JAR
        let download_url = format!("{}/downloads/{}", OPTIFINE_DOWNLOAD_BASE, optifine_id);
        let resolved = self.client.resolve_github_url(&download_url);

        let jar_path = instance_dir.join(format!("OptiFine_{}.jar", optifine_id));
        tokio::fs::create_dir_all(instance_dir).await?;

        log::info!("下载 OptiFine: {} {}", optifine_name, resolved);
        self.client.download_file(&resolved, &jar_path, None::<fn(u64, u64)>).await?;

        // 构建 version.json (OptiFine 通过继承原版工作)
        let vj = VersionJson {
            id: format!("optifine-{}", optifine_id),
            main_class: "net.minecraft.client.main.Main".into(),
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
                    name: format!("optifine:OptiFine:{}", optifine_id),
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

        log::info!("OptiFine {} 安装完成", optifine_name);
        Ok(vj)
    }
}
