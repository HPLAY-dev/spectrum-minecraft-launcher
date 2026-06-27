use crate::error::CoreResult;
use crate::manifest::ManifestManager;
use reqwest::Client;

pub struct DownloadEngine {
    manifest: ManifestManager,
}

impl DownloadEngine {
    pub fn new(client: Client, use_bmclapi: bool) -> Self {
        Self {
            manifest: ManifestManager::new(client, use_bmclapi),
        }
    }

    pub async fn get_version_list(
        &self,
        include_snapshot: bool,
        include_release: bool,
    ) -> CoreResult<Vec<String>> {
        self.manifest
            .get_version_list(include_snapshot, include_release)
            .await
    }
}
