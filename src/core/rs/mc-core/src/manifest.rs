use crate::error::{CoreError, CoreResult};
use reqwest::Client;
use serde::Deserialize;

const MOJANG_MANIFEST: &str = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json";
const BMCL_MANIFEST: &str = "https://bmclapi2.bangbang93.com/mc/game/version_manifest_v2.json";

#[derive(Debug, Deserialize)]
struct VersionManifest {
    versions: Vec<VersionEntry>,
}

#[derive(Debug, Deserialize)]
struct VersionEntry {
    id: String,
    #[serde(rename = "type")]
    version_type: String,
}

pub struct ManifestManager {
    client: Client,
    use_bmclapi: bool,
}

impl ManifestManager {
    pub fn new(client: Client, use_bmclapi: bool) -> Self {
        Self { client, use_bmclapi }
    }

    pub async fn get_version_list(
        &self,
        include_snapshot: bool,
        include_release: bool,
    ) -> CoreResult<Vec<String>> {
        let url = if self.use_bmclapi {
            BMCL_MANIFEST
        } else {
            MOJANG_MANIFEST
        };
        let manifest: VersionManifest = self
            .client
            .get(url)
            .send()
            .await
            .map_err(|e| CoreError::Http(e.to_string()))?
            .json()
            .await
            .map_err(|e| CoreError::Http(e.to_string()))?;

        Ok(manifest
            .versions
            .into_iter()
            .filter(|entry| match entry.version_type.as_str() {
                "release" => include_release,
                "snapshot" => include_snapshot,
                _ => false,
            })
            .map(|entry| entry.id)
            .collect())
    }
}
