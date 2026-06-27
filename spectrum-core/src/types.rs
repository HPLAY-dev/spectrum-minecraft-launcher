//! # 核心类型定义
//!
//! Minecraft 版本 JSON、启动配置、错误类型及平台工具函数。

use serde::{Deserialize, Deserializer, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

// ========================================================================
//  错误类型
// ========================================================================

pub type CoreResult<T> = Result<T, CoreError>;

#[derive(Debug, thiserror::Error)]
pub enum CoreError {
    #[error("IO 错误: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON 错误: {0}")]
    Json(#[from] serde_json::Error),
    #[error("HTTP 错误: {0}")]
    Http(#[from] reqwest::Error),
    #[error("网络错误: {0}")]
    Network(String),
    #[error("版本未找到: {0}")]
    VersionNotFound(String),
    #[error("Java 未找到: {0}")]
    JavaNotFound(String),
    #[error("OAuth 错误: {0}")]
    OAuth(String),
    #[error("安装器错误: {0}")]
    Installer(String),
    #[error("XML 错误: {0}")]
    Xml(String),
    #[error("无效参数: {0}")]
    InvalidArgument(String),
    #[error("Maven 坐标错误: {0}")]
    Maven(String),
    #[error("未知错误: {0}")]
    Unknown(String),
    #[error("ZIP 错误: {0}")]
    Zip(#[from] zip::result::ZipError),
}

// ========================================================================
//  版本清单
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionManifest {
    pub latest: ManifestLatest,
    pub versions: Vec<ManifestVersionEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestLatest {
    pub release: String,
    pub snapshot: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestVersionEntry {
    pub id: String,
    #[serde(rename = "type")]
    pub version_type: String,
    pub url: String,
    #[serde(default)]
    pub time: Option<String>,
    #[serde(default, rename = "releaseTime")]
    pub release_time: Option<String>,
    #[serde(default)]
    pub sha1: Option<String>,
}

// ========================================================================
//  版本 JSON
// ========================================================================

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct VersionJson {
    pub id: String,
    #[serde(default, rename = "inheritsFrom")]
    pub inherits_from: Option<String>,
    #[serde(default, rename = "mainClass")]
    pub main_class: String,
    #[serde(default)]
    pub libraries: Vec<Library>,
    #[serde(default)]
    pub assets: Option<String>,
    #[serde(default, rename = "assetIndex")]
    pub asset_index: Option<AssetIndex>,
    #[serde(default)]
    pub arguments: Option<Arguments>,
    #[serde(default, rename = "minecraftArguments")]
    pub minecraft_arguments: Option<String>,
    #[serde(default, rename = "javaVersion")]
    pub java_version: Option<JavaVersion>,
    #[serde(default)]
    pub downloads: Option<VersionDownloads>,
    #[serde(default, rename = "releaseTime")]
    pub release_time: Option<String>,
    #[serde(default)]
    pub time: Option<String>,
    #[serde(default, rename = "minimumLauncherVersion")]
    pub minimum_launcher_version: Option<i32>,
    #[serde(default)]
    pub logging: Option<LoggingConfig>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct JavaVersion {
    #[serde(default, rename = "majorVersion")]
    pub major_version: i32,
    #[serde(default)]
    pub component: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionDownloads {
    #[serde(default)]
    pub client: Option<ClientDownload>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientDownload {
    pub sha1: String,
    pub size: u64,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetIndex {
    pub id: String,
    pub sha1: String,
    pub size: u64,
    #[serde(default, rename = "totalSize")]
    pub total_size: u64,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Arguments {
    #[serde(default, deserialize_with = "deserialize_arguments")]
    pub game: Vec<Argument>,
    #[serde(default, deserialize_with = "deserialize_arguments")]
    pub jvm: Vec<Argument>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(untagged)]
pub enum Argument {
    Value(String),
    Rules {
        rules: Vec<Rule>,
        value: ArgumentValue,
    },
}

#[derive(Debug, Clone, Serialize)]
#[serde(untagged)]
pub enum ArgumentValue {
    Single(String),
    Multi(Vec<String>),
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Library {
    pub name: String,
    #[serde(default)]
    pub downloads: Option<LibraryDownloads>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub rules: Option<Vec<Rule>>,
    #[serde(default)]
    pub natives: Option<HashMap<String, String>>,
    #[serde(default)]
    pub extract: Option<ExtractRule>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LibraryDownloads {
    #[serde(default)]
    pub artifact: Option<ArtifactDownload>,
    #[serde(default)]
    pub classifiers: Option<HashMap<String, ArtifactDownload>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactDownload {
    pub path: String,
    pub sha1: String,
    pub url: String,
    #[serde(default)]
    pub size: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    pub action: String,
    #[serde(default)]
    pub os: Option<OsRule>,
    #[serde(default)]
    pub features: Option<HashMap<String, bool>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsRule {
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub arch: Option<String>,
    #[serde(default)]
    pub version: Option<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExtractRule {
    #[serde(default)]
    pub exclude: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    #[serde(default)]
    pub client: Option<LoggingClient>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingClient {
    pub argument: String,
    #[serde(default, rename = "type")]
    pub log_type: Option<String>,
    pub file: LoggingFile,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingFile {
    pub id: String,
    pub sha1: String,
    pub size: u64,
    pub url: String,
}

// ========================================================================
//  资源索引
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetIndexData {
    pub objects: HashMap<String, AssetObject>,
    #[serde(default, rename = "virtual")]
    pub virtual_path: Option<bool>,
    #[serde(default, rename = "map_to_resources")]
    pub map_to_resources: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetObject {
    pub hash: String,
    pub size: u64,
}

// ========================================================================
//  启动配置
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LaunchConfig {
    pub java_path: String,
    pub xmx: String,
    pub xms: String,
    pub minecraft_dir: PathBuf,
    pub instance_name: String,
    pub username: String,
    pub uuid: String,
    pub access_token: String,
    pub user_type: String,
    pub version_type: String,
    pub game_directory: PathBuf,
    pub assets_directory: PathBuf,
    pub libraries_directory: PathBuf,
    pub natives_directory: PathBuf,
    pub width: u32,
    pub height: u32,
    pub extra_jvm_args: String,
    pub extra_game_args: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub server_ip: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub server_port: Option<u16>,
}

impl Default for LaunchConfig {
    fn default() -> Self {
        Self {
            java_path: String::new(),
            xmx: "2048M".into(),
            xms: "1024M".into(),
            minecraft_dir: PathBuf::new(),
            instance_name: String::new(),
            username: String::new(),
            uuid: String::new(),
            access_token: String::new(),
            user_type: "mojang".into(),
            version_type: "release".into(),
            game_directory: PathBuf::new(),
            assets_directory: PathBuf::new(),
            libraries_directory: PathBuf::new(),
            natives_directory: PathBuf::new(),
            width: 854,
            height: 480,
            extra_jvm_args: String::new(),
            extra_game_args: String::new(),
            server_ip: None,
            server_port: None,
        }
    }
}

// ========================================================================
//  账户 & OAuth
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Account {
    pub name: String,
    #[serde(rename = "type")]
    pub account_type: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub refresh_token: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub uuid: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OAuthResult {
    pub access_token: String,
    pub refresh_token: String,
    pub uuid: String,
    pub username: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JavaInstallation {
    pub path: PathBuf,
    pub major_version: i32,
    pub full_version: String,
    pub is_jre: bool,
}

// ========================================================================
//  ModLoader
// ========================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ModLoader {
    Vanilla,
    Fabric,
    Forge,
    NeoForge,
    OptiFine,
    LabyMod,
}

impl ModLoader {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "fabric" => Self::Fabric,
            "forge" => Self::Forge,
            "neoforge" => Self::NeoForge,
            "optifine" => Self::OptiFine,
            "labymod" => Self::LabyMod,
            _ => Self::Vanilla,
        }
    }
}

// ========================================================================
//  下载事件
// ========================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DownloadStage {
    FetchingManifest,
    VersionJson,
    ClientJar,
    Libraries,
    Assets,
    ModLoader,
}

impl std::fmt::Display for DownloadStage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::FetchingManifest => "fetching_manifest",
            Self::VersionJson => "version_json",
            Self::ClientJar => "client_jar",
            Self::Libraries => "libraries",
            Self::Assets => "assets",
            Self::ModLoader => "modloader",
        };
        write!(f, "{s}")
    }
}

#[derive(Debug, Clone)]
pub enum DownloadEvent {
    Progress {
        stage: DownloadStage,
        current: u64,
        total: u64,
    },
    FileCompleted {
        name: String,
        success: bool,
    },
    Completed,
    Error(String),
}

// ========================================================================
//  平台工具函数
// ========================================================================

/// 返回当前操作系统名称 (windows / macos / linux)
pub fn native_os() -> &'static str {
    if cfg!(target_os = "windows") {
        "windows"
    } else if cfg!(target_os = "macos") {
        "macos"
    } else {
        "linux"
    }
}

/// 返回 CPU 架构 (用于 Minecraft natives classifier)
pub fn get_architecture() -> &'static str {
    if cfg!(target_arch = "x86_64") {
        "x86_64"
    } else if cfg!(target_arch = "x86") {
        "x86"
    } else if cfg!(target_arch = "aarch64") {
        if cfg!(target_os = "linux") {
            "aarch_64"
        } else {
            "arm64"
        }
    } else if cfg!(target_arch = "arm") {
        "arm"
    } else {
        "x86_64"
    }
}

/// 返回 CPU 架构 (用于 library rules 匹配)
pub fn java_arch() -> &'static str {
    match get_architecture() {
        "x86_64" => "x86",
        "aarch_64" | "arm64" => "arm",
        other => other,
    }
}

/// version.json 中 `os.name` 与当前平台是否匹配（Mojang 使用 `osx` 而非 `macos`）
pub fn rule_os_name_matches(rule_name: &str) -> bool {
    match rule_name {
        "windows" => cfg!(target_os = "windows"),
        "osx" => cfg!(target_os = "macos"),
        "linux" => cfg!(target_os = "linux"),
        other => native_os() == other,
    }
}

/// 判断带 rules 的 JVM 参数 / 库是否适用于当前平台。
/// 若存在 rules 但无一匹配当前 OS，则视为不适用（避免 macOS 专用参数泄漏到 Windows）。
pub fn rules_compatible(rules: &[Rule]) -> bool {
    if rules.is_empty() {
        return true;
    }

    let mut allowed = false;
    let mut matched = false;

    for rule in rules {
        let matches_os = match &rule.os {
            Some(os) => {
                os.name
                    .as_ref()
                    .map_or(true, |n| rule_os_name_matches(n))
                    && os.arch.as_ref().map_or(true, |a| a == java_arch())
            }
            None => true,
        };

        let matches_features = rule
            .features
            .as_ref()
            .map(|f| f.iter().all(|(_, req)| !req))
            .unwrap_or(true);

        if matches_os && matches_features {
            allowed = rule.action == "allow";
            matched = true;
        }
    }

    if matched {
        allowed
    } else {
        false
    }
}

/// 系统位数 "32" / "64"
pub fn get_system_bits() -> &'static str {
    if cfg!(target_pointer_width = "64") {
        "64"
    } else {
        "32"
    }
}

/// OS-arch 组合键，如 `windows-x86_64`
pub fn get_architecture_key() -> String {
    format!("{}-{}", native_os(), get_architecture())
}

/// natives classifier 查找顺序（与 Python tool_funcs 一致）
pub fn native_classifier_keys() -> Vec<String> {
    vec![
        format!("natives-{}", get_architecture_key()),
        format!("natives-{}-{}", native_os(), get_system_bits()),
        format!("natives-{}", native_os()),
        format!("natives-{}", get_architecture()),
    ]
}

/// 将 Maven 坐标转换为相对路径
pub fn maven_to_path(maven_str: &str) -> CoreResult<String> {
    let mut packaging = "jar";
    let mut raw = maven_str;

    if let Some((left, right)) = raw.rsplit_once('@') {
        raw = left;
        packaging = right;
    }

    let parts: Vec<&str> = raw.split(':').collect();
    if parts.len() < 3 {
        return Err(CoreError::Maven(format!(
            "无效的 Maven 坐标: {}",
            maven_str
        )));
    }

    let group_id = parts[0];
    let artifact_id = parts[1];
    let version = parts[2];
    let classifier = if parts.len() >= 4 && !parts[3].is_empty() {
        Some(parts[3])
    } else {
        None
    };

    let group_path = group_id.replace('.', "/");
    let mut filename = format!("{}-{}", artifact_id, version);
    if let Some(c) = classifier {
        filename.push('-');
        filename.push_str(c);
    }
    filename.push('.');
    filename.push_str(packaging);

    Ok(format!("{}/{}/{}/{}", group_path, artifact_id, version, filename))
}

// ========================================================================
//  Argument 反序列化 (Minecraft 混合格式)
// ========================================================================

fn deserialize_arguments<'de, D>(deserializer: D) -> Result<Vec<Argument>, D::Error>
where
    D: Deserializer<'de>,
{
    use serde::de::Error;
    let values: Vec<serde_json::Value> = Vec::deserialize(deserializer)?;
    values
        .into_iter()
        .map(|value| parse_argument(value).map_err(D::Error::custom))
        .collect()
}

fn parse_argument(value: serde_json::Value) -> Result<Argument, String> {
    match value {
        serde_json::Value::String(s) => Ok(Argument::Value(s)),
        serde_json::Value::Object(map) => {
            let rules: Vec<Rule> = map
                .get("rules")
                .map(|v| serde_json::from_value(v.clone()))
                .transpose()
                .map_err(|e| e.to_string())?
                .unwrap_or_default();

            let arg_value = map
                .get("value")
                .cloned()
                .ok_or_else(|| "argument object missing 'value' field".to_string())?;

            let value = match arg_value {
                serde_json::Value::String(s) => ArgumentValue::Single(s),
                serde_json::Value::Array(arr) => ArgumentValue::Multi(
                    arr.into_iter()
                        .filter_map(|v| v.as_str().map(String::from))
                        .collect(),
                ),
                other => {
                    return Err(format!("unexpected argument value type: {other}"));
                }
            };

            Ok(Argument::Rules { rules, value })
        }
        other => Err(format!("unexpected argument type: {other}")),
    }
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_maven_to_path() {
        let path = maven_to_path("com.mojang:authlib:1.5.25").unwrap();
        assert_eq!(
            path,
            "com/mojang/authlib/1.5.25/authlib-1.5.25.jar"
        );
    }

    #[test]
    fn test_maven_to_path_with_classifier() {
        let path = maven_to_path("org.lwjgl:lwjgl:3.3.1:natives-windows").unwrap();
        assert_eq!(
            path,
            "org/lwjgl/lwjgl/3.3.1/lwjgl-3.3.1-natives-windows.jar"
        );
    }

    #[test]
    fn test_modloader_from_str() {
        assert_eq!(ModLoader::from_str("fabric"), ModLoader::Fabric);
        assert_eq!(ModLoader::from_str("NeoForge"), ModLoader::NeoForge);
        assert_eq!(ModLoader::from_str("unknown"), ModLoader::Vanilla);
    }
}
