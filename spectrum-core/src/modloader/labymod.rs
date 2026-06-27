//! # LabyMod 4 安装器

#[path = "labymod4.rs"]
mod labymod4;
pub use labymod4::LabyMod4Installer;

use super::ModLoaderInstaller;
use crate::http_client::HttpClient;
use crate::types::*;
use async_trait::async_trait;
use std::path::Path;

pub struct LabyModInstaller {
    inner: LabyMod4Installer,
}

impl LabyModInstaller {
    pub fn new(client: HttpClient) -> Self {
        Self {
            inner: LabyMod4Installer::new(client),
        }
    }
}

#[async_trait]
impl ModLoaderInstaller for LabyModInstaller {
    fn name(&self) -> &'static str {
        "LabyMod"
    }

    async fn get_supported_versions(&self) -> CoreResult<Vec<String>> {
        self.inner.get_versions().await
    }

    async fn get_loader_versions(&self, _mc_version: &str) -> CoreResult<Vec<String>> {
        Ok(vec!["4".into()])
    }

    async fn install(
        &self,
        mc_version: &str,
        loader_version: Option<&str>,
        instance_dir: &Path,
        minecraft_dir: &Path,
    ) -> CoreResult<VersionJson> {
        let instance_name = instance_dir
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("labymod");
        let lv: i32 = loader_version.and_then(|s| s.parse().ok()).unwrap_or(4);
        self.inner
            .download(minecraft_dir, lv, mc_version, instance_name)
            .await?;

        let json_path = instance_dir.join(format!("{instance_name}.json"));
        let content = tokio::fs::read_to_string(&json_path).await?;
        serde_json::from_str(&content).map_err(CoreError::Json)
    }
}
