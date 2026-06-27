//! # 下载引擎
//!
//! 异步并发下载 — 等价 Python `download_funcs.py` 的 `auto_download` 流程。
//!
//! - 版本 JSON（含 ModLoader 安装）
//! - Client JAR
//! - Libraries + Natives 解压
//! - Assets

use crate::http_client::HttpClient;
use crate::manifest::{AssetIndexManager, ManifestManager, VersionJsonManager};
use crate::modloader;
use crate::natives::{extract_natives_archive, flatten_natives_dir, natives_dir, pick_native_artifact};
use crate::types::*;

use std::path::Path;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use tokio::sync::mpsc;
use tokio::sync::Semaphore;
use sha1::{Digest, Sha1};

/// 下载结果
#[derive(Debug, Clone)]
pub enum DownloadResult {
    Success,
    AlreadyExists,
    Error(String),
}

/// 一键下载选项 — 对应 Python `auto_download` 参数
#[derive(Debug, Clone)]
pub struct AutoDownloadOptions {
    pub mc_version: String,
    pub instance_name: String,
    pub modloader: ModLoader,
    pub modloader_version: Option<String>,
}

/// 下载引擎
#[derive(Debug, Clone)]
pub struct DownloadEngine {
    client: HttpClient,
    manifest_mgr: ManifestManager,
    version_json_mgr: VersionJsonManager,
    concurrency: Arc<Semaphore>,
}

impl DownloadEngine {
    pub fn new(client: HttpClient) -> Self {
        let concurrency = Arc::new(Semaphore::new(8));
        Self {
            manifest_mgr: ManifestManager::new(client.clone()),
            version_json_mgr: VersionJsonManager::new(client.clone()),
            client,
            concurrency,
        }
    }

    pub async fn get_version_list(
        &mut self,
        snapshot: bool,
        old_alpha: bool,
        old_beta: bool,
        release: bool,
    ) -> CoreResult<Vec<String>> {
        self.manifest_mgr
            .get_version_list(snapshot, old_alpha, old_beta, release)
            .await
    }

    pub async fn get_latest_release(&mut self) -> CoreResult<String> {
        self.manifest_mgr.get_latest_release().await
    }

    pub async fn get_latest_snapshot(&mut self) -> CoreResult<String> {
        self.manifest_mgr.get_latest_snapshot().await
    }

    /// 下载完整 Minecraft 版本（FFI 入口）
    pub async fn download_version(
        &mut self,
        mc_version: &str,
        instance_name: &str,
        minecraft_dir: &Path,
        modloader: ModLoader,
        tx: mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<DownloadResult> {
        self.auto_download(
            minecraft_dir,
            AutoDownloadOptions {
                mc_version: mc_version.to_string(),
                instance_name: instance_name.to_string(),
                modloader,
                modloader_version: None,
            },
            tx,
        )
        .await
    }

    /// 一键下载 — 等价 Python `auto_download`
    pub async fn auto_download(
        &mut self,
        minecraft_dir: &Path,
        opts: AutoDownloadOptions,
        tx: mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<DownloadResult> {
        let instance_dir = minecraft_dir.join("versions").join(&opts.instance_name);
        let json_path = instance_dir.join(format!("{}.json", opts.instance_name));

        tokio::fs::create_dir_all(&instance_dir).await?;

        // ========== 1. 版本 JSON（含 ModLoader 首次安装）==========
        tx.send(DownloadEvent::Progress {
            stage: DownloadStage::FetchingManifest,
            current: 0,
            total: 1,
        })
        .await
        .map_err(|_| CoreError::Unknown("channel closed".into()))?;

        if self.needs_version_json_install(&json_path, &opts).await? {
            self.install_version_json(minecraft_dir, &instance_dir, &opts, &tx)
                .await?;
        }

        tx.send(DownloadEvent::Progress {
            stage: DownloadStage::VersionJson,
            current: 1,
            total: 1,
        })
        .await
        .map_err(|_| CoreError::Unknown("channel closed".into()))?;

        // 合并 inheritsFrom 链，得到完整依赖清单
        let merged = self
            .version_json_mgr
            .resolve_instance_json(&json_path, &mut self.manifest_mgr)
            .await?;

        self.sync_instance_artifacts(
            minecraft_dir,
            &instance_dir,
            &opts.instance_name,
            &merged,
            &tx,
        )
        .await?;

        tx.send(DownloadEvent::Completed)
            .await
            .map_err(|_| CoreError::Unknown("channel closed".into()))?;

        Ok(DownloadResult::Success)
    }

    /// 下载 client.jar、libraries、assets（JSON 已就绪时）
    async fn sync_instance_artifacts(
        &self,
        minecraft_dir: &Path,
        instance_dir: &Path,
        instance_name: &str,
        merged: &VersionJson,
        tx: &mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<()> {
        if let Some(ref client_download) = merged.downloads.as_ref().and_then(|d| d.client.as_ref()) {
            tx.send(DownloadEvent::Progress {
                stage: DownloadStage::ClientJar,
                current: 0,
                total: 1,
            })
            .await
            .map_err(|_| CoreError::Unknown("channel closed".into()))?;

            let jar_path = instance_dir.join(format!("{instance_name}.jar"));
            let resolved_url = self.client.resolve_url(&client_download.url);

            if !jar_path.exists()
                || !self.verify_sha1(&jar_path, &client_download.sha1).await?
            {
                self.client
                    .download_file(
                        &resolved_url,
                        &jar_path,
                        Some(|current, total| {
                            let _ = tx.try_send(DownloadEvent::Progress {
                                stage: DownloadStage::ClientJar,
                                current,
                                total,
                            });
                        }),
                    )
                    .await?;
            }

            tx.send(DownloadEvent::Progress {
                stage: DownloadStage::ClientJar,
                current: 1,
                total: 1,
            })
            .await
            .map_err(|_| CoreError::Unknown("channel closed".into()))?;
        }

        let lib_dir = minecraft_dir.join("libraries");
        self.download_libraries(merged, &lib_dir, instance_dir, instance_name, tx)
            .await?;

        if let Some(ref asset_index) = merged.asset_index {
            let assets_dir = minecraft_dir.join("assets");
            self.download_assets(asset_index, &assets_dir, tx).await?;
        }

        Ok(())
    }

    /// 启动前补全缺失的 libraries / client.jar / assets
    pub async fn ensure_instance_libraries(
        &mut self,
        minecraft_dir: &Path,
        instance_name: &str,
    ) -> CoreResult<()> {
        let instance_dir = minecraft_dir.join("versions").join(instance_name);
        let json_path = instance_dir.join(format!("{instance_name}.json"));
        if !json_path.exists() {
            return Ok(());
        }

        let merged = self
            .version_json_mgr
            .resolve_instance_json(&json_path, &mut self.manifest_mgr)
            .await?;

        let lib_dir = minecraft_dir.join("libraries");
        let missing = Self::count_missing_libraries(&merged, &lib_dir);
        let jar_path = instance_dir.join(format!("{instance_name}.jar"));
        let client_missing = merged
            .downloads
            .as_ref()
            .and_then(|d| d.client.as_ref())
            .is_some_and(|_| !jar_path.exists());

        if missing == 0 && !client_missing {
            return Ok(());
        }

        log::info!(
            "实例 {instance_name} 缺少 {missing} 个库{}，正在补全…",
            if client_missing { " 及 client.jar" } else { "" }
        );

        let (tx, mut rx) = mpsc::channel::<DownloadEvent>(32);
        tokio::spawn(async move {
            while rx.recv().await.is_some() {}
        });

        self.sync_instance_artifacts(
            minecraft_dir,
            &instance_dir,
            instance_name,
            &merged,
            &tx,
        )
        .await
    }

    fn count_missing_libraries(version_json: &VersionJson, lib_dir: &Path) -> usize {
        version_json
            .libraries
            .iter()
            .filter(|lib| Self::is_library_compatible(lib))
            .filter(|lib| {
                if let Some(ref dl) = lib.downloads {
                    if let Some(ref artifact) = dl.artifact {
                        return !lib_dir.join(&artifact.path).exists();
                    }
                }
                if let Ok(maven_path) = maven_to_path(&lib.name) {
                    return !lib_dir.join(&maven_path).exists();
                }
                false
            })
            .count()
    }

    /// 启动前修复：实例名暗示 ModLoader 但 JSON 仍是原版配置
    pub async fn repair_modloader_json_if_needed(
        &mut self,
        minecraft_dir: &Path,
        instance_name: &str,
    ) -> CoreResult<bool> {
        let instance_dir = minecraft_dir.join("versions").join(instance_name);
        let json_path = instance_dir.join(format!("{instance_name}.json"));
        if !json_path.exists() {
            return Ok(false);
        }

        let content = tokio::fs::read_to_string(&json_path).await?;
        let raw: VersionJson = serde_json::from_str(&content)?;
        if !modloader::instance_json::is_vanilla_launch_profile(&raw) {
            return Ok(false);
        }

        let Some(loader) = modloader::instance_json::guess_modloader_from_name(instance_name) else {
            return Ok(false);
        };

        let mc_version = modloader::instance_json::guess_mc_version(instance_name, &raw);
        log::info!(
            "检测到 {instance_name} 缺少 ModLoader 配置，正在安装 {:?}…",
            loader
        );

        let opts = AutoDownloadOptions {
            mc_version,
            instance_name: instance_name.to_string(),
            modloader: loader,
            modloader_version: None,
        };

        let (tx, mut rx) = mpsc::channel::<DownloadEvent>(32);
        tokio::spawn(async move {
            while rx.recv().await.is_some() {}
        });

        self.install_version_json(minecraft_dir, &instance_dir, &opts, &tx)
            .await?;

        let merged = self
            .version_json_mgr
            .resolve_instance_json(&json_path, &mut self.manifest_mgr)
            .await?;
        self.sync_instance_artifacts(
            minecraft_dir,
            &instance_dir,
            instance_name,
            &merged,
            &tx,
        )
        .await?;

        Ok(true)
    }

    /// 是否需要写入/修复 version JSON
    async fn needs_version_json_install(
        &self,
        json_path: &Path,
        opts: &AutoDownloadOptions,
    ) -> CoreResult<bool> {
        if !json_path.exists() {
            return Ok(true);
        }
        if opts.modloader == ModLoader::Vanilla {
            return Ok(false);
        }
        let content = tokio::fs::read_to_string(json_path).await?;
        let existing: VersionJson = serde_json::from_str(&content)?;
        let detected = modloader::instance_json::detect_modloader_in_json(&existing);
        Ok(detected != opts.modloader)
    }

    /// 首次安装或修复：写入合并后的 version JSON（Vanilla 或 ModLoader）
    async fn install_version_json(
        &mut self,
        minecraft_dir: &Path,
        instance_dir: &Path,
        opts: &AutoDownloadOptions,
        tx: &mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<()> {
        let json_path = instance_dir.join(format!("{}.json", opts.instance_name));

        match opts.modloader {
            ModLoader::Vanilla => {
                let mut vj = self
                    .version_json_mgr
                    .get_version_json(&opts.mc_version, &mut self.manifest_mgr)
                    .await?;
                vj.id = opts.instance_name.clone();
                self.version_json_mgr.save_to_file(&vj, &json_path).await?;
            }
            loader => {
                tx.send(DownloadEvent::Progress {
                    stage: DownloadStage::ModLoader,
                    current: 0,
                    total: 1,
                })
                .await
                .map_err(|_| CoreError::Unknown("channel closed".into()))?;

                let installer = modloader::get_installer(self.client.clone(), loader).ok_or_else(|| {
                    CoreError::Installer(format!("不支持的 ModLoader: {loader:?}"))
                })?;

                let loader_vj = installer
                    .install(
                        &opts.mc_version,
                        opts.modloader_version.as_deref(),
                        instance_dir,
                        minecraft_dir,
                    )
                    .await
                    .map_err(|e| {
                        log::error!("ModLoader 安装失败: {e}");
                        CoreError::Installer(format!("ModLoader 安装失败: {e}"))
                    })?;

                modloader::instance_json::merge_and_save_instance_json(
                    &mut self.version_json_mgr,
                    &mut self.manifest_mgr,
                    loader_vj,
                    &opts.mc_version,
                    &opts.instance_name,
                    &json_path,
                )
                .await?;

                tx.send(DownloadEvent::Progress {
                    stage: DownloadStage::ModLoader,
                    current: 1,
                    total: 1,
                })
                .await
                .map_err(|_| CoreError::Unknown("channel closed".into()))?;
            }
        }

        Ok(())
    }

    // ====================================================================
    //  Libraries + Natives
    // ====================================================================

    async fn download_libraries(
        &self,
        version_json: &VersionJson,
        lib_dir: &Path,
        instance_dir: &Path,
        instance_name: &str,
        tx: &mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<()> {
        let total = version_json.libraries.len() as u64;
        tx.send(DownloadEvent::Progress {
            stage: DownloadStage::Libraries,
            current: 0,
            total,
        })
        .await
        .map_err(|_| CoreError::Unknown("channel closed".into()))?;

        let natives_path = natives_dir(instance_dir, instance_name);
        tokio::fs::create_dir_all(&natives_path).await?;

        let mut completed = 0u64;
        let mut handles = Vec::new();

        for lib in &version_json.libraries {
            if !Self::is_library_compatible(lib) {
                completed += 1;
                continue;
            }

            let client = self.client.clone();
            let lib_dir = lib_dir.to_path_buf();
            let instance_dir = instance_dir.to_path_buf();
            let instance_name = instance_name.to_string();
            let natives_path = natives_path.clone();
            let lib = lib.clone();
            let tx = tx.clone();
            let permit = self
                .concurrency
                .clone()
                .acquire_owned()
                .await
                .map_err(|e| CoreError::Unknown(e.to_string()))?;

            handles.push(tokio::spawn(async move {
                let _permit = permit;
                let result = Self::download_single_library(
                    &client,
                    &lib,
                    &lib_dir,
                    &instance_dir,
                    &instance_name,
                    &natives_path,
                )
                .await;

                let name = lib.name.clone();
                let success = result.is_ok();
                let _ = tx
                    .send(DownloadEvent::FileCompleted { name, success })
                    .await;

                result
            }));
        }

        for handle in handles {
            if let Err(e) = handle.await {
                log::error!("库下载任务失败: {e}");
            }
            completed += 1;
            let _ = tx
                .send(DownloadEvent::Progress {
                    stage: DownloadStage::Libraries,
                    current: completed,
                    total,
                })
                .await;
        }

        // 扁平化 natives（与 Python download_libraries 末尾一致）
        flatten_natives_dir(&natives_path).await?;

        Ok(())
    }

    async fn download_single_library(
        client: &HttpClient,
        lib: &Library,
        lib_dir: &Path,
        _instance_dir: &Path,
        _instance_name: &str,
        natives_path: &Path,
    ) -> CoreResult<()> {
        let is_native_lib = lib.natives.is_some()
            || lib.name.contains("natives-")
            || lib.name.contains(":natives:");

        // 1. 下载主 artifact
        if let Some(ref downloads) = lib.downloads {
            if let Some(ref artifact) = downloads.artifact {
                Self::download_artifact(client, lib_dir, artifact).await?;
            }

            // 2. 下载并解压 natives classifier
            if let Some(ref classifiers) = downloads.classifiers {
                if lib.natives.is_some() || is_native_lib {
                    if let Some(native_artifact) = pick_native_artifact(classifiers) {
                        let native_jar = lib_dir.join(&native_artifact.path);
                        Self::download_artifact(client, lib_dir, native_artifact).await?;

                        let exclude = lib
                            .extract
                            .as_ref()
                            .map(|e| e.exclude.clone())
                            .unwrap_or_default();
                        extract_natives_archive(&native_jar, natives_path, &exclude).await?;
                    }
                }
            }
        } else if let Ok(maven_path) = maven_to_path(&lib.name) {
            // 旧版 fallback
            let base_url = lib
                .url
                .as_deref()
                .unwrap_or("https://libraries.minecraft.net/");
            let base_url = if base_url.ends_with('/') {
                base_url.to_string()
            } else {
                format!("{base_url}/")
            };
            let url = format!("{base_url}{maven_path}");
            let resolved_url = client.resolve_url(&url);
            let lib_path = lib_dir.join(&maven_path);

            if !lib_path.exists() {
                if let Some(parent) = lib_path.parent() {
                    tokio::fs::create_dir_all(parent).await?;
                }
                match client
                    .download_file(&resolved_url, &lib_path, None::<fn(u64, u64)>)
                    .await
                {
                    Ok(_) => {}
                    Err(CoreError::VersionNotFound(_)) | Err(CoreError::Network(_)) => {
                        log::warn!("库下载失败(跳过): {}", lib.name);
                    }
                    Err(e) => return Err(e),
                }
            }
        }

        Ok(())
    }

    async fn download_artifact(
        client: &HttpClient,
        lib_dir: &Path,
        artifact: &ArtifactDownload,
    ) -> CoreResult<()> {
        let lib_path = lib_dir.join(&artifact.path);

        if lib_path.exists() {
            if Self::verify_sha1_file(&lib_path, &artifact.sha1)
                .await
                .unwrap_or(false)
            {
                return Ok(());
            }
        }

        if let Some(parent) = lib_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        let resolved_url = client.resolve_url(&artifact.url);
        client
            .download_file(&resolved_url, &lib_path, None::<fn(u64, u64)>)
            .await
    }

    fn is_library_compatible(lib: &Library) -> bool {
        if let Some(ref rules) = lib.rules {
            if !rules_compatible(rules) {
                return false;
            }
        }

        if let Some(ref natives) = lib.natives {
            let os_name = native_os();
            let os_key = match os_name {
                "windows" => "windows",
                "macos" => "osx",
                _ => os_name,
            };
            if !natives.contains_key(os_key) && !natives.contains_key(os_name) {
                return false;
            }
        }

        true
    }

    // ====================================================================
    //  Assets
    // ====================================================================

    async fn download_assets(
        &self,
        asset_index_info: &AssetIndex,
        assets_dir: &Path,
        tx: &mpsc::Sender<DownloadEvent>,
    ) -> CoreResult<()> {
        let indexes_dir = assets_dir.join("indexes");
        let index_path = indexes_dir.join(format!("{}.json", asset_index_info.id));

        tokio::fs::create_dir_all(&indexes_dir).await?;

        let resolved_url = self.client.resolve_url(&asset_index_info.url);

        if !index_path.exists()
            || !self
                .verify_sha1(&index_path, &asset_index_info.sha1)
                .await?
        {
            self.client
                .download_file(&resolved_url, &index_path, None::<fn(u64, u64)>)
                .await?;
        }

        let index_data = AssetIndexManager::load_from_file(&index_path).await?;
        let total = index_data.objects.len() as u64;

        tx.send(DownloadEvent::Progress {
            stage: DownloadStage::Assets,
            current: 0,
            total,
        })
        .await
        .map_err(|_| CoreError::Unknown("channel closed".into()))?;

        let completed = Arc::new(AtomicU64::new(0));
        let mut handles = Vec::with_capacity(index_data.objects.len());

        // 在任务内部 acquire 并发许可，避免父循环串行等待导致长时间停在 [AST][0/N]。
        for (_, obj) in &index_data.objects {
            let client = self.client.clone();
            let assets_dir = assets_dir.to_path_buf();
            let hash = obj.hash.clone();
            let concurrency = self.concurrency.clone();
            let tx = tx.clone();
            let completed = Arc::clone(&completed);

            handles.push(tokio::spawn(async move {
                let _permit = concurrency
                    .acquire_owned()
                    .await
                    .map_err(|e| CoreError::Unknown(e.to_string()))?;

                let result = Self::download_single_asset(&client, &assets_dir, &hash).await;

                let n = completed.fetch_add(1, Ordering::Relaxed) + 1;
                // 节流进度上报，避免 5000+ 事件塞满 channel 或拖慢 UI
                if n == 1 || n == total || n % 20 == 0 {
                    let _ = tx
                        .try_send(DownloadEvent::Progress {
                            stage: DownloadStage::Assets,
                            current: n,
                            total,
                        });
                }

                result
            }));
        }

        for handle in handles {
            if let Err(e) = handle.await {
                log::error!("资源下载任务失败: {e}");
            }
        }

        Ok(())
    }

    async fn download_single_asset(
        client: &HttpClient,
        assets_dir: &Path,
        hash: &str,
    ) -> CoreResult<()> {
        let object_dir = assets_dir.join("objects").join(&hash[..2]);
        let object_path = object_dir.join(hash);

        if object_path.exists() {
            if Self::verify_sha1_file(object_path.as_path(), hash)
                .await
                .unwrap_or(false)
            {
                return Ok(());
            }
        }

        let url = if client.use_bmclapi() {
            format!(
                "https://bmclapi2.bangbang93.com/assets/{}/{}",
                &hash[..2],
                hash
            )
        } else {
            format!(
                "https://resources.download.minecraft.net/{}/{}",
                &hash[..2],
                hash
            )
        };

        tokio::fs::create_dir_all(&object_dir).await?;
        client
            .download_file(&url, &object_path, None::<fn(u64, u64)>)
            .await
    }

    // ====================================================================
    //  SHA1
    // ====================================================================

    pub async fn verify_sha1(&self, path: &Path, expected: &str) -> CoreResult<bool> {
        Self::verify_sha1_file(path, expected).await
    }

    async fn verify_sha1_file(path: &Path, expected_hex: &str) -> CoreResult<bool> {
        if !path.exists() {
            return Ok(false);
        }
        let data = tokio::fs::read(path).await?;
        let mut hasher = Sha1::new();
        hasher.update(&data);
        Ok(format!("{:x}", hasher.finalize()) == expected_hex.to_lowercase())
    }

    pub async fn compute_sha1(path: &Path) -> CoreResult<String> {
        let data = tokio::fs::read(path).await?;
        let mut hasher = Sha1::new();
        hasher.update(&data);
        Ok(format!("{:x}", hasher.finalize()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_library_compatible() {
        let lib_all_os = Library {
            name: "net.minecraft:launchwrapper:1.12".into(),
            ..Default::default()
        };
        assert!(DownloadEngine::is_library_compatible(&lib_all_os));
    }
}
