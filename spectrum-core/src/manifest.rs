//! # 版本清单管理
//!
//! 负责获取 Minecraft 版本清单和解析版本 JSON。
//! 对应原 Python: `manifest_funcs.py` + `download_funcs.py` 中的版本列表部分。

use crate::http_client::HttpClient;
use crate::modloader::instance_json;
use crate::types::*;

/// 版本清单 URL (Mojang 官方)
const MOJANG_MANIFEST_URL: &str =
    "https://piston-meta.mojang.com/mc/game/version_manifest.json";

/// 版本清单 URL (BMCLAPI 镜像)
const BMCLAPI_MANIFEST_URL: &str =
    "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json";

/// 版本清单管理器
#[derive(Debug, Clone)]
pub struct ManifestManager {
    client: HttpClient,
    /// 缓存已获取的版本清单
    cached_manifest: Option<VersionManifest>,
}

impl ManifestManager {
    pub fn new(client: HttpClient) -> Self {
        Self {
            client,
            cached_manifest: None,
        }
    }

    /// 获取版本清单 URL
    fn manifest_url(&self) -> &str {
        if self.client.use_bmclapi() {
            BMCLAPI_MANIFEST_URL
        } else {
            MOJANG_MANIFEST_URL
        }
    }

    /// 获取版本清单 (带缓存)
    pub async fn get_manifest(&mut self) -> CoreResult<&VersionManifest> {
        if self.cached_manifest.is_none() {
            let manifest_url = self.manifest_url();
            log::info!("获取版本清单: {}", manifest_url);
            let manifest: VersionManifest = self.client.get_json(manifest_url).await?;
            self.cached_manifest = Some(manifest);
        }
        Ok(self.cached_manifest.as_ref().unwrap())
    }

    /// 强制刷新版本清单
    pub async fn refresh_manifest(&mut self) -> CoreResult<&VersionManifest> {
        self.cached_manifest = None;
        self.get_manifest().await
    }

    /// 获取版本列表 (过滤后的字符串列表)
    pub async fn get_version_list(
        &mut self,
        include_snapshot: bool,
        include_old_alpha: bool,
        include_old_beta: bool,
        include_release: bool,
    ) -> CoreResult<Vec<String>> {
        let manifest = self.get_manifest().await?;

        let mut versions: Vec<String> = manifest
            .versions
            .iter()
            .filter(|entry| {
                let is_release = entry.version_type == "release";
                let is_snapshot = entry.version_type == "snapshot";
                let is_old_alpha = entry.version_type == "old_alpha";
                let is_old_beta = entry.version_type == "old_beta";

                (include_release && is_release)
                    || (include_snapshot && is_snapshot)
                    || (include_old_alpha && is_old_alpha)
                    || (include_old_beta && is_old_beta)
            })
            .map(|entry| entry.id.clone())
            .collect();

        // 反向排序: 新版本在前
        versions.reverse();
        Ok(versions)
    }

    /// 获取最新正式版 ID
    pub async fn get_latest_release(&mut self) -> CoreResult<String> {
        let manifest = self.get_manifest().await?;
        Ok(manifest.latest.release.clone())
    }

    /// 获取最新快照版 ID
    pub async fn get_latest_snapshot(&mut self) -> CoreResult<String> {
        let manifest = self.get_manifest().await?;
        Ok(manifest.latest.snapshot.clone())
    }

    /// 获取单个版本在清单中的入口信息
    pub async fn get_version_entry(
        &mut self,
        version_id: &str,
    ) -> CoreResult<ManifestVersionEntry> {
        let manifest = self.get_manifest().await?;

        manifest
            .versions
            .iter()
            .find(|entry| entry.id == version_id)
            .cloned()
            .ok_or_else(|| {
                CoreError::VersionNotFound(format!("版本 '{}' 未在清单中找到", version_id))
            })
    }

    /// 获取版本清单中所有版本的完整列表 (用于外部过滤)
    pub async fn get_all_versions(&mut self) -> CoreResult<Vec<ManifestVersionEntry>> {
        let manifest = self.get_manifest().await?;
        Ok(manifest.versions.clone())
    }
}

// ========================================================================
//  版本 JSON 下载与解析
// ========================================================================

/// 版本 JSON 管理器
#[derive(Debug, Clone)]
pub struct VersionJsonManager {
    client: HttpClient,
    /// 缓存: version_id → VersionJson
    cache: std::collections::HashMap<String, VersionJson>,
}

impl VersionJsonManager {
    pub fn new(client: HttpClient) -> Self {
        Self {
            client,
            cache: std::collections::HashMap::new(),
        }
    }

    /// 从本地文件加载版本 JSON
    pub async fn load_from_file(path: &std::path::Path) -> CoreResult<VersionJson> {
        let content = tokio::fs::read_to_string(path).await?;
        let vj: VersionJson = serde_json::from_str(&content)?;
        Ok(vj)
    }

    /// 从 URL 下载版本 JSON
    pub async fn download_from_url(&self, url: &str) -> CoreResult<VersionJson> {
        log::info!("下载版本 JSON: {}", url);
        let resolved_url = self.client.resolve_url(url);
        let vj: VersionJson = self.client.get_json(&resolved_url).await?;
        Ok(vj)
    }

    /// 从版本清单下载版本 JSON (带缓存)
    pub async fn get_version_json(
        &mut self,
        version_id: &str,
        manifest_mgr: &mut ManifestManager,
    ) -> CoreResult<VersionJson> {
        if let Some(cached) = self.cache.get(version_id) {
            return Ok(cached.clone());
        }

        // 收集继承链 (子 → 根)，避免递归 async
        let mut chain: Vec<VersionJson> = Vec::new();
        let mut current_id = version_id.to_string();

        loop {
            if let Some(cached) = self.cache.get(&current_id) {
                chain.push(cached.clone());
                break;
            }

            let entry = manifest_mgr.get_version_entry(&current_id).await?;
            let vj = self.download_from_url(&entry.url).await?;
            let parent_id = vj.inherits_from.clone();
            chain.push(vj);

            match parent_id {
                Some(pid) => current_id = pid,
                None => break,
            }
        }

        // 从根向子合并
        let mut merged = chain.pop().unwrap();
        while let Some(child) = chain.pop() {
            merged = VersionJsonManager::merge_version_json(child, merged)?;
        }

        self.cache.insert(version_id.to_string(), merged.clone());
        Ok(merged)
    }

    /// 解析本地实例 version.json，合并 inheritsFrom 父版本
    pub async fn resolve_instance_json(
        &mut self,
        json_path: &std::path::Path,
        manifest_mgr: &mut ManifestManager,
    ) -> CoreResult<VersionJson> {
        let content = tokio::fs::read_to_string(json_path).await?;
        let child: VersionJson = serde_json::from_str(&content)?;

        if let Some(ref parent_id) = child.inherits_from {
            let parent = self.get_version_json(parent_id, manifest_mgr).await?;
            VersionJsonManager::merge_version_json(child, parent)
        } else if instance_json::needs_vanilla_metadata(&child) {
            let mc_version = instance_json::guess_mc_version_from_json(&child);
            let parent = self.get_version_json(&mc_version, manifest_mgr).await?;
            VersionJsonManager::merge_version_json(child, parent)
        } else {
            Ok(child)
        }
    }

    /// 从 version JSON 推断 Minecraft 基版本 ID
    pub fn get_minecraft_version(vj: &VersionJson) -> String {
        crate::modloader::instance_json::guess_mc_version_from_json(vj)
    }

    /// 获取 version JSON 要求的 Java 主版本
    pub fn get_required_java_version(vj: &VersionJson) -> i32 {
        vj.java_version
            .as_ref()
            .map(|jv| jv.major_version)
            .unwrap_or(8)
    }

    /// 保存版本 JSON 到本地文件
    pub async fn save_to_file(
        &self,
        vj: &VersionJson,
        path: &std::path::Path,
    ) -> CoreResult<()> {
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        let content = serde_json::to_string_pretty(vj)?;
        tokio::fs::write(path, content).await?;
        Ok(())
    }

    // ====================================================================
    //  JSON 合并 (深度合并)
    // ====================================================================

    /// 深度合并两个 VersionJson
    /// child 是修饰版本 (如 Forge), parent 是父版本 (如 1.19.2 原版)
    pub fn merge_version_json(child: VersionJson, parent: VersionJson) -> CoreResult<VersionJson> {
        let merged_libraries = Self::merge_libraries(
            parent.libraries.clone(),
            child.libraries.clone(),
        );

        let merged_arguments = match (parent.arguments, child.arguments) {
            (Some(p), Some(c)) => Some(Self::merge_arguments(p, c)),
            (Some(p), None) => Some(p),
            (None, Some(c)) => Some(c),
            (None, None) => None,
        };

        Ok(VersionJson {
            id: child.id.clone(),
            inherits_from: child.inherits_from.clone(),
            main_class: child.main_class.clone(),
            libraries: merged_libraries,
            assets: child.assets.clone().or(parent.assets.clone()),
            asset_index: child.asset_index.clone().or(parent.asset_index.clone()),
            arguments: merged_arguments,
            minecraft_arguments: child.minecraft_arguments.clone()
                .or(parent.minecraft_arguments.clone()),
            java_version: child.java_version.clone().or(parent.java_version),
            downloads: child.downloads.clone().or(parent.downloads),
            release_time: child.release_time.clone().or(parent.release_time),
            time: child.time.clone().or(parent.time),
            minimum_launcher_version: child.minimum_launcher_version
                .or(parent.minimum_launcher_version),
            logging: child.logging.clone().or(parent.logging),
        })
    }

    /// 合并 Libraries: 子条目优先, 按 name 去重
    fn merge_libraries(parent: Vec<Library>, child: Vec<Library>) -> Vec<Library> {
        let mut merged = Vec::new();
        let mut seen = std::collections::HashSet::new();

        // 先插入子版本 (Forge) 的库, 优先级高
        for lib in child {
            let key = lib.name.clone();
            if !seen.contains(&key) {
                merged.push(lib);
                seen.insert(key);
            }
        }

        // 再插入父版本 (原版) 的库, 跳过已存在的
        for lib in parent {
            let key = lib.name.clone();
            if !seen.contains(&key) {
                merged.push(lib);
                seen.insert(key);
            }
        }

        merged
    }

    /// 合并 Arguments
    fn merge_arguments(parent: Arguments, child: Arguments) -> Arguments {
        Arguments {
            game: Self::merge_argument_lists(parent.game, child.game),
            jvm: Self::merge_argument_lists(parent.jvm, child.jvm),
        }
    }

    fn merge_argument_lists(parent: Vec<Argument>, child: Vec<Argument>) -> Vec<Argument> {
        let mut merged = child;
        merged.extend(parent);
        merged
    }
}

// ========================================================================
//  资源文件索引 (assets/indexes)
// ========================================================================

/// 资源文件索引管理器
#[derive(Debug, Clone)]
pub struct AssetIndexManager;

impl AssetIndexManager {
    /// 下载并解析资源文件索引
    pub async fn download_index(
        client: &HttpClient,
        index_url: &str,
    ) -> CoreResult<AssetIndexData> {
        let resolved = client.resolve_url(index_url);
        let data: AssetIndexData = client.get_json(&resolved).await?;
        Ok(data)
    }

    /// 从本地加载资源索引
    pub async fn load_from_file(path: &std::path::Path) -> CoreResult<AssetIndexData> {
        let content = tokio::fs::read_to_string(path).await?;
        let data: AssetIndexData = serde_json::from_str(&content)?;
        Ok(data)
    }

    /// 保存资源索引
    pub async fn save_to_file(
        data: &AssetIndexData,
        path: &std::path::Path,
    ) -> CoreResult<()> {
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        let content = serde_json::to_string_pretty(data)?;
        tokio::fs::write(path, content).await?;
        Ok(())
    }
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merge_libraries_dedup() {
        let parent = vec![
            Library {
                name: "net.minecraft:client:1.19".into(),
                ..default_lib()
            },
            Library {
                name: "org.lwjgl:lwjgl:3.3.1".into(),
                ..default_lib()
            },
        ];
        let child = vec![
            Library {
                name: "net.minecraftforge:forge:1.19-41.0.0".into(),
                ..default_lib()
            },
            Library {
                name: "org.lwjgl:lwjgl:3.3.1".into(), // 重复，应跳过
                ..default_lib()
            },
        ];

        let merged = VersionJsonManager::merge_libraries(parent, child);
        assert_eq!(merged.len(), 3); // 3 个不重复
        assert_eq!(merged[0].name, "net.minecraftforge:forge:1.19-41.0.0");
    }

    fn default_lib() -> Library {
        Library {
            name: String::new(),
            downloads: None,
            url: None,
            rules: None,
            natives: None,
            extract: None,
        }
    }
}
