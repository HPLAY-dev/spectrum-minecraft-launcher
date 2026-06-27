//! # Forge ModLoader 安装器
//!
//! 从 Forge Maven 获取元数据、下载安装器、生成版本 JSON。
//! 支持新版 Forge (1.13+) 和旧版 Forge (1.5-1.12.2)。

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use quick_xml::Reader;
use quick_xml::events::Event;
use std::path::Path;

/// Forge Maven 仓库
const FORGE_MAVEN: &str = "https://maven.minecraftforge.net";

pub struct ForgeInstaller {
    client: HttpClient,
}

impl ForgeInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    /// 解析 Maven Metadata XML 获取可用版本
    async fn fetch_maven_metadata(&self, artifact_path: &str) -> CoreResult<Vec<String>> {
        let url = format!("{}/{}/maven-metadata.xml", FORGE_MAVEN, artifact_path);
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

        // 反向排序 (最新版本在前)
        versions.reverse();
        Ok(versions)
    }

    /// 解析 Forge 版本号为可比较的结构
    fn parse_forge_version(version: &str) -> Option<(i32, i32, i32)> {
        let parts: Vec<&str> = version.split('.').collect();
        if parts.len() < 3 {
            return None;
        }
        Some((
            parts[0].parse().ok()?,
            parts[1].parse().ok()?,
            parts[2].parse().ok()?,
        ))
    }
}

#[async_trait]
impl ModLoaderInstaller for ForgeInstaller {
    fn name(&self) -> &'static str {
        "Forge"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        // 从 Forge Maven 获取 Minecraft 版本列表
        let versions = self.fetch_maven_metadata("net/minecraftforge/forge").await?;
        let mut mc_versions: Vec<String> = versions.iter()
            .filter_map(|v| {
                // Forge 版本格式: mcVersion-loaderVersion
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
        let forge_versions = self.fetch_maven_metadata("net/minecraftforge/forge").await?;

        // 过滤出该 Minecraft 版本的 Forge 版本
        let prefix = format!("{}-", mc_version);
        let mut versions: Vec<String> = forge_versions.iter()
            .filter(|v| v.starts_with(&prefix))
            .map(|v| v[prefix.len()..].to_string())
            .collect();

        versions.sort_by(|a, b| {
            let ap = Self::parse_forge_version(a);
            let bp = Self::parse_forge_version(b);
            bp.cmp(&ap) // 降序
        });

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
                versions.first().cloned()
                    .ok_or_else(|| CoreError::Installer(
                        format!("Forge 不支持 Minecraft {}", mc_version)
                    ))?
            }
        };

        let forge_full_version = format!("{}-{}", mc_version, lv);

        // 1. 下载安装器 JAR
        let installer_url = format!(
            "{}/net/minecraftforge/forge/{}/forge-{}-installer.jar",
            FORGE_MAVEN, forge_full_version, forge_full_version
        );
        let resolved_url = self.client.resolve_url(&installer_url);

        let installer_dir = minecraft_dir.join("cache").join("installers");
        tokio::fs::create_dir_all(&installer_dir).await?;
        let installer_path = installer_dir.join(format!("forge-{}-installer.jar", forge_full_version));

        if !installer_path.exists() {
            log::info!("下载 Forge 安装器: {}", forge_full_version);
            self.client.download_file(
                &resolved_url,
                &installer_path,
                None::<fn(u64, u64)>,
            ).await?;
        }

        // 2. 尝试从 ZIP 中提取 version.json (新版 Forge 把文件直接打包在安装器里)
        let vj = Self::extract_version_from_installer(&installer_path, mc_version, &forge_full_version)
            .or_else(|_| {
                log::warn!("无法从安装器提取 version.json, 使用 Universal JAR 模式");
                Self::build_universal_version_json(mc_version, &forge_full_version)
            })?;

        // 3. 保存 version.json
        let json_path = instance_dir.join(format!("{}.json", &vj.id));
        tokio::fs::create_dir_all(instance_dir).await?;
        let content = serde_json::to_string_pretty(&vj)?;
        tokio::fs::write(&json_path, content).await?;

        // 4. 复制 Forge JAR
        let forge_jar_name = format!("forge-{}-universal.jar", forge_full_version);
        let forge_jar_src = installer_dir.join(&forge_jar_name);
        if !forge_jar_src.exists() {
            // 尝试从安装器提取 universal jar
            if let Ok(jar_data) = Self::extract_universal_jar(&installer_path) {
                tokio::fs::write(&forge_jar_src, &jar_data).await?;
            }
        }

        log::info!("Forge {} 安装完成", forge_full_version);
        Ok(vj)
    }
}

impl ForgeInstaller {
    /// 从安装器 JAR 中提取 version.json
    fn extract_version_from_installer(
        installer_path: &Path,
        mc_version: &str,
        forge_version: &str,
    ) -> CoreResult<VersionJson> {
        let file = std::fs::File::open(installer_path)?;
        let mut archive = zip::ZipArchive::new(file)?;

        // 可能的位置
        let paths = [
            format!("version.json"),
            format!("{}-{}.json", mc_version, forge_version),
        ];

        for path in &paths {
            if let Ok(mut file) = archive.by_name(path) {
                let mut content = String::new();
                use std::io::Read;
                file.read_to_string(&mut content)?;
                let mut vj: VersionJson = serde_json::from_str(&content)?;
                vj.id = format!("forge-{}", forge_version);
                return Ok(vj);
            }
        }

        Err(CoreError::Installer("未在安装器中找到 version.json".into()))
    }

    /// 从安装器提取 universal JAR
    fn extract_universal_jar(installer_path: &Path) -> CoreResult<Vec<u8>> {
        let file = std::fs::File::open(installer_path)?;
        let mut archive = zip::ZipArchive::new(file)?;

        let paths = ["forge-1.12.2-14.23.5.2860-universal.jar", "maven/net/minecraftforge/forge/1.12.2-14.23.5.2860/forge-1.12.2-14.23.5.2860-universal.jar"];

        for path in &paths {
            if let Ok(mut file) = archive.by_name(path) {
                let mut data = Vec::new();
                use std::io::Read;
                file.read_to_end(&mut data)?;
                return Ok(data);
            }
        }

        Err(CoreError::Installer("未找到 universal JAR".into()))
    }

    /// 构建 Universal JAR 模式的 version.json (旧版 Forge)
    fn build_universal_version_json(_mc_version: &str, forge_version: &str) -> CoreResult<VersionJson> {
        Ok(VersionJson {
            id: format!("forge-{}", forge_version),
            main_class: "net.minecraft.launchwrapper.Launch".into(),
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
                    name: format!("net.minecraftforge:forge:{}:universal", forge_version),
                    ..Default::default()
                },
                Library {
                    name: "net.minecraft:launchwrapper:1.12".into(),
                    ..Default::default()
                },
                Library {
                    name: "org.ow2.asm:asm-all:5.2".into(),
                    ..Default::default()
                },
                Library {
                    name: format!("net.minecraftforge:forge:{}", forge_version),
                    ..Default::default()
                },
            ],
            ..Default::default()
        })
    }
}
