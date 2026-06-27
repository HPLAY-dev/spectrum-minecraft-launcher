//! LabyMod 4（releases.r2.labymod.net）

use crate::http_client::HttpClient;
use crate::types::*;
use serde_json::{json, Value};
use std::path::Path;

const API_BASE: &str = "https://releases.r2.labymod.net/api/v1/";

pub struct LabyMod4Installer {
    client: HttpClient,
    release_type: String,
}

impl LabyMod4Installer {
    pub fn new(client: HttpClient) -> Self {
        Self {
            client,
            release_type: "production".into(),
        }
    }

    fn api_url(&self, path: &str) -> String {
        format!("{API_BASE}{path}")
    }

    async fn fetch_manifest(&self) -> CoreResult<Value> {
        let url = self.api_url(&format!("manifest/{}/latest.json", self.release_type));
        let resolved = self.client.resolve_url(&url);
        self.client.get_json(&resolved).await
    }

    async fn fetch_library_api(&self) -> CoreResult<Value> {
        let url = self.api_url(&format!("libraries/{}.json", self.release_type));
        let resolved = self.client.resolve_url(&url);
        self.client.get_json(&resolved).await
    }

    pub async fn get_versions(&self) -> CoreResult<Vec<String>> {
        let manifest = self.fetch_manifest().await?;
        let mut versions = Vec::new();
        if let Some(arr) = manifest["minecraftVersions"].as_array() {
            for entry in arr {
                if let Some(v) = entry["version"].as_str() {
                    versions.push(v.to_string());
                }
            }
        }
        Ok(versions)
    }

    async fn download_file(&self, url: &str, path: &Path) -> CoreResult<()> {
        if path.exists() {
            return Ok(());
        }
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        log::info!("下载 LabyMod: {} -> {}", url, path.display());
        self.client
            .download_file(url, path, None::<fn(u64, u64)>)
            .await
    }

    pub async fn download(
        &self,
        minecraft_dir: &Path,
        labymod_version: i32,
        mc_version: &str,
        instance_name: &str,
    ) -> CoreResult<()> {
        let manifest = self.fetch_manifest().await?;
        let commit = manifest["commitReference"]
            .as_str()
            .ok_or_else(|| CoreError::Installer("LabyMod manifest 缺少 commitReference".into()))?
            .to_string();
        let laby_mod_version = manifest["labyModVersion"]
            .as_str()
            .unwrap_or("4")
            .to_string();
        let sha1 = manifest["sha1"].as_str().unwrap_or("").to_string();

        let library_api = self.fetch_library_api().await?;
        let libraries = library_api["libraries"]
            .as_array()
            .cloned()
            .unwrap_or_default();

        for lib in &libraries {
            let url = lib["url"]
                .as_str()
                .ok_or_else(|| CoreError::Installer(format!("无效 library: {lib}")))?;
            if !url.starts_with("https://releases.r2.labymod.net/") {
                return Err(CoreError::Installer(format!("不支持的 library URL: {url}")));
            }
            let rel = url.trim_start_matches("https://releases.r2.labymod.net/");
            let path = minecraft_dir.join(rel.replace('/', std::path::MAIN_SEPARATOR_STR));
            self.download_file(url, &path).await?;
        }

        let jar_path = minecraft_dir.join(format!(
            "libraries/net/labymod/LabyMod/{labymod_version}/LabyMod-{labymod_version}.jar"
        ));
        let jar_url = self.api_url(&format!(
            "download/labymod4/{}/{commit}.jar",
            self.release_type
        ));
        self.download_file(&jar_url, &jar_path).await?;

        if let Some(assets) = manifest["assets"].as_object() {
            for (name, hash) in assets {
                let asset_path = minecraft_dir.join(format!(
                    "versions/{instance_name}/labymod-neo/assets/{name}.jar"
                ));
                let asset_url = self.api_url(&format!(
                    "download/assets/labymod4/{}/{}/{name}/{}.jar",
                    self.release_type,
                    commit,
                    hash.as_str().unwrap_or("")
                ));
                self.download_file(&asset_url, &asset_path).await?;
            }
        }

        let mc_entry = manifest["minecraftVersions"]
            .as_array()
            .and_then(|arr| arr.iter().find(|e| e["version"].as_str() == Some(mc_version)))
            .ok_or_else(|| CoreError::Installer(format!("LabyMod 不支持 Minecraft {mc_version}")))?;

        let profile_id = format!("LabyMod-4-{commit}");
        let version_type = mc_entry["type"].as_str().unwrap_or("release");

        let mut version_json: Value = if mc_entry.get("customManifestUrl").is_some() {
            let custom_url = mc_entry["customManifestUrl"]
                .as_str()
                .ok_or_else(|| CoreError::Installer("缺少 customManifestUrl".into()))?;
            let resolved = self.client.resolve_url(custom_url);
            self.client.get_json(&resolved).await?
        } else {
            return Err(CoreError::Installer("旧版 LabyMod 安装路径未实现".into()));
        };

        if let Some(obj) = version_json.as_object_mut() {
            obj.insert("id".into(), json!(profile_id));
            obj.insert(
                "labymod_data".into(),
                json!({
                    "channelType": self.release_type,
                    "version": laby_mod_version,
                    "versionType": version_type,
                    "commitReference": commit,
                }),
            );
            let mut libs = obj
                .get("libraries")
                .and_then(|v| v.as_array())
                .cloned()
                .unwrap_or_default();
            libs.push(json!({
                "name": "net.labymod:LabyMod:4",
                "url": format!("{API_BASE}download/labymod4/{}/{commit}.jar", self.release_type),
                "sha1": sha1,
            }));
            for lib in libraries {
                libs.push(lib);
            }
            obj.insert("libraries".into(), Value::Array(libs));
        }

        let instance_dir = minecraft_dir.join("versions").join(instance_name);
        tokio::fs::create_dir_all(&instance_dir).await?;
        let json_path = instance_dir.join(format!("{instance_name}.json"));
        let content = serde_json::to_string_pretty(&version_json)?;
        tokio::fs::write(json_path, content).await?;

        log::info!("LabyMod 4 安装完成: {instance_name}");
        Ok(())
    }
}
