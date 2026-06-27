//! # 核心数据结构
//!
//! 所有跨模块共享的类型定义。

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::fmt;
use thiserror::Error;

// ========================================================================
//  错误类型
// ========================================================================

/// 全局错误枚举
#[derive(Debug, Error)]
pub enum CoreError {
    #[error("HTTP 请求失败: {0}")]
    Http(#[from] reqwest::Error),

    #[error("IO 错误: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON 解析错误: {0}")]
    Json(#[from] serde_json::Error),

    #[error("XML 解析错误: {0}")]
    Xml(String),

    #[error("OAuth 认证失败: {0}")]
    OAuth(String),

    #[error("版本未找到: {0}")]
    VersionNotFound(String),

    #[error("Java 未找到: {0}")]
    JavaNotFound(String),

    #[error("安装程序错误: {0}")]
    Installer(String),

    #[error("参数不合法: {0}")]
    InvalidArgument(String),

    #[error("网络不可达: {0}")]
    Network(String),

    #[error("未知错误: {0}")]
    Unknown(String),
}

/// 专用 Result 别名
pub type CoreResult<T> = Result<T, CoreError>;

// ========================================================================
//  版本清单 (version_manifest.json)
// ========================================================================

/// 版本清单根结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionManifest {
    pub latest: LatestVersions,
    pub versions: Vec<ManifestVersionEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LatestVersions {
    pub release: String,
    pub snapshot: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestVersionEntry {
    pub id: String,
    #[serde(rename = "type")]
    pub version_type: String,
    pub url: String,
    pub time: String,
    #[serde(rename = "releaseTime")]
    pub release_time: String,
    #[serde(default)]
    pub sha1: Option<String>,
    #[serde(default)]
    pub compliance_level: Option<i32>,
}

// ========================================================================
//  版本 JSON (version.json)
// ========================================================================

/// 每个 Minecraft 版本的完整描述 (version.json)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionJson {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    #[serde(rename = "inheritsFrom")]
    pub inherits_from: Option<String>,
    #[serde(rename = "mainClass")]
    pub main_class: String,
    #[serde(default)]
    pub libraries: Vec<Library>,
    #[serde(default)]
    pub assets: Option<String>,
    #[serde(rename = "assetIndex")]
    #[serde(default)]
    pub asset_index: Option<AssetIndex>,
    #[serde(default)]
    pub arguments: Option<Arguments>,
    #[serde(rename = "minecraftArguments")]
    #[serde(default)]
    pub minecraft_arguments: Option<String>,
    #[serde(rename = "javaVersion")]
    #[serde(default)]
    pub java_version: Option<JavaVersion>,
    #[serde(default)]
    pub downloads: Option<Downloads>,
    #[serde(rename = "releaseTime")]
    #[serde(default)]
    pub release_time: Option<String>,
    #[serde(default)]
    pub time: Option<String>,
    #[serde(rename = "minimumLauncherVersion")]
    #[serde(default)]
    pub minimum_launcher_version: Option<i32>,
    #[serde(default)]
    pub logging: Option<Logging>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetIndex {
    pub id: String,
    pub sha1: String,
    pub size: u64,
    pub total_size: u64,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JavaVersion {
    #[serde(rename = "majorVersion")]
    pub major_version: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Downloads {
    #[serde(default)]
    pub client: Option<DownloadEntry>,
    #[serde(default)]
    pub server: Option<DownloadEntry>,
    #[serde(default)]
    pub client_mappings: Option<DownloadEntry>,
    #[serde(default)]
    pub server_mappings: Option<DownloadEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadEntry {
    pub sha1: String,
    pub size: u64,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Logging {
    pub client: LoggingClient,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingClient {
    pub argument: String,
    pub file: DownloadEntry,
    #[serde(rename = "type")]
    pub log_type: String,
}

// ========================================================================
//  库 (Library)
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Library {
    pub name: String,
    #[serde(default)]
    pub downloads: Option<LibraryDownloads>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub rules: Option<Vec<Rule>>,
    #[serde(default)]
    pub natives: Option<std::collections::HashMap<String, String>>,
    #[serde(default)]
    pub extract: Option<Extract>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LibraryDownloads {
    #[serde(default)]
    pub artifact: Option<Artifact>,
    #[serde(default)]
    pub classifiers: Option<std::collections::HashMap<String, Artifact>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub path: String,
    pub sha1: String,
    pub size: u64,
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    pub action: String,
    #[serde(default)]
    pub os: Option<OsRule>,
    #[serde(default)]
    pub features: Option<std::collections::HashMap<String, bool>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OsRule {
    pub name: Option<String>,
    pub arch: Option<String>,
    pub version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Extract {
    pub exclude: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Arguments {
    #[serde(default)]
    pub game: Vec<Argument>,
    #[serde(default)]
    pub jvm: Vec<Argument>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Argument {
    Value(String),
    Rules {
        rules: Vec<Rule>,
        value: ArgumentValue,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ArgumentValue {
    Single(String),
    Multi(Vec<String>),
}

// ========================================================================
//  启动配置
// ========================================================================

/// 启动 Minecraft 所需的所有配置
#[derive(Debug, Clone)]
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
    pub server_ip: Option<String>,
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
            username: "Player".into(),
            uuid: String::new(),
            access_token: String::new(),
            user_type: "mojang".into(),
            version_type: "Spectrum Launcher".into(),
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
//  账户类型
// ========================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Account {
    #[serde(rename = "offline")]
    Offline { name: String },
    #[serde(rename = "microsoft")]
    Microsoft {
        name: String,
        uuid: String,
        refresh_token: String,
    },
}

impl Account {
    pub fn name(&self) -> &str {
        match self {
            Account::Offline { name } => name,
            Account::Microsoft { name, .. } => name,
        }
    }
}

// ========================================================================
//  ModLoader 类型
// ========================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ModLoader {
    Vanilla,
    Fabric,
    Forge,
    NeoForge,
    LabyMod,
    OptiFine,
}

impl ModLoader {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "fabric" => ModLoader::Fabric,
            "forge" => ModLoader::Forge,
            "neoforge" => ModLoader::NeoForge,
            "labymod" => ModLoader::LabyMod,
            "optifine" => ModLoader::OptiFine,
            _ => ModLoader::Vanilla,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            ModLoader::Vanilla => "vanilla",
            ModLoader::Fabric => "fabric",
            ModLoader::Forge => "forge",
            ModLoader::NeoForge => "neoforge",
            ModLoader::LabyMod => "labymod",
            ModLoader::OptiFine => "optifine",
        }
    }
}

impl fmt::Display for ModLoader {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

// ========================================================================
//  下载进度事件
// ========================================================================

/// 下载过程中的进度报告
#[derive(Debug, Clone)]
pub enum DownloadEvent {
    /// 进度更新 (当前数量, 总数, 阶段描述)
    Progress {
        stage: DownloadStage,
        current: u64,
        total: u64,
    },
    /// 单个文件下载完成
    FileCompleted {
        name: String,
        success: bool,
    },
    /// 整个任务完成
    Completed,
    /// 错误发生
    Error(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DownloadStage {
    /// 获取版本清单
    FetchingManifest,
    /// 下载版本 JSON
    VersionJson,
    /// 下载客户端 JAR
    ClientJar,
    /// 下载库依赖
    Libraries,
    /// 下载资源文件
    Assets,
    /// 安装 ModLoader
    ModLoader,
    /// 下载 ModLoader 文件
    ModLoaderFiles,
    /// 检查文件完整性
    Verifying,
    /// 完成
    Finished,
}

impl fmt::Display for DownloadStage {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DownloadStage::FetchingManifest => write!(f, "FETCHING_MANIFEST"),
            DownloadStage::VersionJson => write!(f, "JSON"),
            DownloadStage::ClientJar => write!(f, "JAR"),
            DownloadStage::Libraries => write!(f, "LIB"),
            DownloadStage::Assets => write!(f, "AST"),
            DownloadStage::ModLoader => write!(f, "MODLOADER"),
            DownloadStage::ModLoaderFiles => write!(f, "MODFILES"),
            DownloadStage::Verifying => write!(f, "VERIFY"),
            DownloadStage::Finished => write!(f, "DONE"),
        }
    }
}

// ========================================================================
//  OAuth 结果
// ========================================================================

/// Microsoft OAuth 认证结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OAuthResult {
    pub access_token: String,
    pub refresh_token: String,
    pub uuid: String,
    pub username: String,
}

// ========================================================================
//  Java 安装信息
// ========================================================================

#[derive(Debug, Clone)]
pub struct JavaInstallation {
    pub path: PathBuf,
    pub major_version: i32,
    pub full_version: String,
    pub is_jre: bool,
}

// ========================================================================
//  平台工具函数
// ========================================================================

/// 获取当前操作系统类型字符串
pub fn native_os() -> &'static str {
    if cfg!(target_os = "windows") {
        "windows"
    } else if cfg!(target_os = "macos") {
        "macos"
    } else {
        "linux"
    }
}

/// 获取架构字符串 (标准化)
pub fn get_architecture() -> String {
    let arch = std::env::consts::ARCH;
    match arch {
        "x86_64" => "x86_64".to_string(),
        "aarch64" => "aarch_64".to_string(),
        "x86" => "x86".to_string(),
        "arm" => "arm".to_string(),
        _ => arch.to_string(),
    }
}

/// 获取系统位宽
pub fn get_system_bits() -> u8 {
    if cfg!(target_pointer_width = "64") {
        64
    } else {
        32
    }
}

/// Java 架构映射
pub fn java_arch() -> &'static str {
    if cfg!(target_arch = "x86_64") {
        "x64"
    } else if cfg!(target_arch = "aarch64") {
        "aarch64"
    } else {
        "x86"
    }
}

/// 将 Maven 坐标转换为路径
/// 例如: `net.minecraft:launchwrapper:1.12` → `net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar`
pub fn maven_to_path(maven_str: &str) -> CoreResult<String> {
    let mut packaging = "jar";
    let raw = if let Some(at_pos) = maven_str.find('@') {
        packaging = &maven_str[at_pos + 1..];
        &maven_str[..at_pos]
    } else {
        maven_str
    };

    let parts: Vec<&str> = raw.split(':').collect();
    if parts.len() < 3 {
        return Err(CoreError::InvalidArgument(format!(
            "无效的 Maven 坐标: '{}'，需要至少 group:artifact:version",
            maven_str
        )));
    }

    let group_id = parts[0];
    let artifact_id = parts[1];
    let version = parts[2];
    let classifier = parts.get(3).filter(|c| !c.is_empty());

    let group_path = group_id.replace('.', "/");

    let mut filename = format!("{}-{}", artifact_id, version);
    if let Some(cls) = classifier {
        filename.push_str(&format!("-{}", cls));
    }
    filename.push_str(&format!(".{}", packaging));

    Ok(format!("{}/{}/{}/{}", group_path, artifact_id, version, filename))
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_maven_to_path() {
        assert_eq!(
            maven_to_path("net.minecraft:launchwrapper:1.12").unwrap(),
            "net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar"
        );
    }

    #[test]
    fn test_maven_to_path_with_classifier() {
        assert_eq!(
            maven_to_path("org.lwjgl:lwjgl:3.2.1:natives-windows").unwrap(),
            "org/lwjgl/lwjgl/3.2.1/lwjgl-3.2.1-natives-windows.jar"
        );
    }

    #[test]
    fn test_maven_to_path_with_packaging() {
        assert_eq!(
            maven_to_path("net.minecraft:client:1.21@zip").unwrap(),
            "net/minecraft/client/1.21/client-1.21.zip"
        );
    }

    #[test]
    fn test_maven_to_path_invalid() {
        assert!(maven_to_path("invalid").is_err());
    }
}
