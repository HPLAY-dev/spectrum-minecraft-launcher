//! # Java 运行时管理
//!
//! 负责:
//! - 检测系统中已安装的 Java
//! - 从 Adoptium/清华镜像下载 Java
//! - Java 版本比较与选择
//!
//! 对应原 Python: `java.py`

use crate::http_client::HttpClient;
use crate::types::*;

use regex::Regex;
use scraper::{Html, Selector};
use std::path::{Path, PathBuf};
use std::process::Command;

/// Java 运行时类型
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum JavaType {
    Jre,
    Jdk,
}

impl JavaType {
    pub fn as_str(&self) -> &'static str {
        match self {
            JavaType::Jre => "jre",
            JavaType::Jdk => "jdk",
        }
    }
}

// ========================================================================
//  Java 检测器
// ========================================================================

/// Java 检测器 — 扫描系统中已安装的 Java
pub struct JavaDetector;

impl JavaDetector {
    /// 查找系统中所有 Java 安装
    pub fn find_all() -> Vec<JavaInstallation> {
        let mut javas = Vec::new();

        // 从 PATH 中查找
        Self::find_from_path(&mut javas);

        // 从注册表查找 (Windows)
        if cfg!(target_os = "windows") {
            Self::find_from_registry(&mut javas);
        }

        // 从常见位置查找 (Linux/macOS)
        Self::find_from_common_locations(&mut javas);

        // 去重并排序 (按版本号降序)
        javas.sort_by(|a, b| b.major_version.cmp(&a.major_version));
        javas.dedup_by(|a, b| a.path == b.path);

        javas
    }

    /// 查找指定大版本的最新 Java
    pub fn find_version(major: i32) -> Option<JavaInstallation> {
        let all = Self::find_all();
        // 优先精确匹配, 然后找最近的
        all.into_iter()
            .filter(|j| j.major_version >= major)
            .min_by_key(|j| j.major_version - major)
    }

    /// 从 PATH 环境变量中查找 Java
    fn find_from_path(javas: &mut Vec<JavaInstallation>) {
        let java_names = if cfg!(target_os = "windows") {
            vec!["javaw.exe", "java.exe", "java"]
        } else {
            vec!["java"]
        };

        if let Ok(paths) = std::env::var("PATH") {
            for dir in std::env::split_paths(&paths) {
                for name in &java_names {
                    let java_path = dir.join(name);
                    if java_path.exists() {
                        if let Some(info) = Self::get_java_info(&java_path) {
                            javas.push(info);
                        }
                    }
                }
            }
        }
    }

    /// 从 Windows 注册表查找 Java
    #[cfg(target_os = "windows")]
    fn find_from_registry(javas: &mut Vec<JavaInstallation>) {
        use winreg::enums::*;
        use winreg::RegKey;

        let paths = [
            r"SOFTWARE\JavaSoft\Java Runtime Environment",
            r"SOFTWARE\JavaSoft\Java Development Kit",
            r"SOFTWARE\JavaSoft\JRE",
            r"SOFTWARE\JavaSoft\JDK",
            r"SOFTWARE\Adoptium\JDK",
            r"SOFTWARE\Adoptium\JRE",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\javaw.exe",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\java.exe",
        ];

        for path in &paths {
            if let Ok(key) = RegKey::predef(HKEY_LOCAL_MACHINE)
                .open_subkey_with_flags(*path, KEY_READ)
                .or_else(|_| RegKey::predef(HKEY_CURRENT_USER).open_subkey_with_flags(*path, KEY_READ))
            {
                // 尝试读取 CurrentVersion 来找到默认版本
                if let Ok(current_version) = key.get_value::<String, _>("CurrentVersion") {
                    if let Ok(version_key) = key.open_subkey(&current_version) {
                        if let Ok(java_home) = version_key.get_value::<String, _>("JavaHome") {
                            let java_path = PathBuf::from(&java_home).join("bin").join("javaw.exe");
                            if java_path.exists() {
                                if let Some(info) = Self::get_java_info(&java_path) {
                                    javas.push(info);
                                }
                            }
                        }
                    }
                }

                // 遍历所有子键
                for name in key.enum_keys().filter_map(|k| k.ok()) {
                    if let Ok(sub_key) = key.open_subkey(&name) {
                        if let Ok(java_home) = sub_key.get_value::<String, _>("JavaHome") {
                            let java_path = PathBuf::from(&java_home).join("bin").join("javaw.exe");
                            if java_path.exists() {
                                if let Some(info) = Self::get_java_info(&java_path) {
                                    javas.push(info);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    #[cfg(not(target_os = "windows"))]
    fn find_from_registry(_javas: &mut Vec<JavaInstallation>) {
        // 非 Windows 系统忽略
    }

    /// 从常见的安装位置查找
    fn find_from_common_locations(javas: &mut Vec<JavaInstallation>) {
        let common_paths = if cfg!(target_os = "windows") {
            vec![
                r"C:\Program Files\Java",
                r"C:\Program Files\Adoptium",
                r"C:\Program Files\Eclipse Adoptium",
                r"C:\Program Files\Eclipse Foundation",
                r"C:\Program Files\Microsoft",
            ]
        } else if cfg!(target_os = "macos") {
            vec![
                "/Library/Java/JavaVirtualMachines",
                "/System/Library/Java/JavaVirtualMachines",
                "/usr/local/opt",
                "/opt/homebrew/opt",
            ]
        } else {
            vec![
                "/usr/lib/jvm",
                "/usr/lib/jvm/java",
                "/usr/local/lib/jvm",
                "/opt/java",
            ]
        };

        for base_path in &common_paths {
            let base = PathBuf::from(base_path);
            if !base.exists() {
                continue;
            }

            if let Ok(entries) = std::fs::read_dir(&base) {
                for entry in entries.flatten() {
                    let java_path = if cfg!(target_os = "windows") {
                        entry.path().join("bin").join("javaw.exe")
                    } else if cfg!(target_os = "macos") {
                        entry.path().join("Contents/Home/bin/java")
                    } else {
                        entry.path().join("bin/java")
                    };

                    if java_path.exists() {
                        if let Some(info) = Self::get_java_info(&java_path) {
                            javas.push(info);
                        }
                    }

                    // 也检查直接是 bin/java 的情况
                    let alt_path = if cfg!(target_os = "windows") {
                        entry.path().join("bin/java.exe")
                    } else {
                        entry.path().join("bin/java")
                    };
                    if alt_path.exists() && alt_path != java_path {
                        if let Some(info) = Self::get_java_info(&alt_path) {
                            javas.push(info);
                        }
                    }
                }
            }
        }
    }

    /// 获取单个 Java 的版本信息
    pub fn get_java_info(java_path: &Path) -> Option<JavaInstallation> {
        let output = Command::new(java_path)
            .arg("-version")
            .output()
            .ok()?;

        let stderr = String::from_utf8_lossy(&output.stderr);
        let stdout = String::from_utf8_lossy(&output.stdout);
        let combined = format!("{}{}", stderr, stdout);

        let (major_version, full_version) = Self::parse_version_output(&combined)?;
        let is_jre = combined.to_lowercase().contains("openjdk")
            || combined.to_lowercase().contains("java se")
            || combined.contains("HotSpot")
            || combined.contains("OpenJDK");

        Some(JavaInstallation {
            path: java_path.to_path_buf(),
            major_version,
            full_version: full_version.clone(),
            is_jre: is_jre || full_version.to_lowercase().contains("jre"),
        })
    }

    /// 解析 Java -version 输出
    fn parse_version_output(output: &str) -> Option<(i32, String)> {
        // "openjdk version "1.8.0_462" 2025-01-21"
        // "openjdk version "21.0.2" 2025-01-21"
        // "java version "17.0.1" 2021-10-19 LTS"

        let re = Regex::new(r#""([\d._]+)""#).ok()?;
        let cap = re.captures(output)?;
        let version_str = cap[1].to_string();
        let parts: Vec<&str> = version_str.split('.').collect();

        let major: i32 = parts[0].parse().ok()?;

        // Java 8 及之前: 1.8.0_xxx → 8
        let result_major = if major == 1 && parts.len() > 1 {
            parts[1].parse::<i32>().ok()?
        } else {
            major
        };

        Some((result_major, version_str))
    }
}

// ========================================================================
//  Java 下载
// ========================================================================

/// Java 下载器 — 从 Adoptium 镜像下载 Java
pub struct JavaDownloader {
    client: HttpClient,
}

impl JavaDownloader {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    /// 获取 Java 下载 URL（tuna=true 清华镜像，false=GitHub Adoptium API）
    pub async fn get_download_url(
        &self,
        version: i32,
        java_type: JavaType,
        use_tuna: bool,
    ) -> CoreResult<String> {
        if use_tuna {
            self.get_download_url_tuna(version, java_type).await
        } else {
            self.get_download_url_github(version, java_type)
                .await?
                .ok_or_else(|| {
                    CoreError::JavaNotFound(format!(
                        "GitHub 未找到 Java {} {}",
                        version,
                        java_type.as_str()
                    ))
                })
        }
    }

    /// GitHub Adoptium releases API
    pub async fn get_download_url_github(
        &self,
        version: i32,
        java_type: JavaType,
    ) -> CoreResult<Option<String>> {
        let feature = if version <= 8 { 8 } else { version };
        let arch = Self::host_arch_adoptium();
        let os = Self::host_os_adoptium();
        let ext = if cfg!(target_os = "windows") {
            ".msi"
        } else {
            ".tar.gz"
        };

        let api_url = format!(
            "https://api.github.com/repos/adoptium/temurin{feature}-binaries/releases/latest"
        );
        let data: serde_json::Value = self
            .client
            .get_json_with_headers(
                &api_url,
                &[("Accept", "application/vnd.github+json")],
            )
            .await?;
        let prefix = format!(
            "OpenJDK{feature}U-{}_{}_{}_hotspot",
            java_type.as_str(),
            arch,
            os
        );

        if let Some(assets) = data["assets"].as_array() {
            for asset in assets {
                if let Some(name) = asset["name"].as_str() {
                    if name.starts_with(&prefix) && name.ends_with(ext) {
                        if let Some(url) = asset["browser_download_url"].as_str() {
                            return Ok(Some(url.to_string()));
                        }
                    }
                }
            }
        }
        Ok(None)
    }

    fn host_arch_adoptium() -> &'static str {
        if cfg!(target_arch = "x86_64") {
            "x64"
        } else if cfg!(target_arch = "aarch64") {
            "aarch64"
        } else {
            "x86"
        }
    }

    fn host_os_adoptium() -> &'static str {
        if cfg!(target_os = "windows") {
            "windows"
        } else if cfg!(target_os = "macos") {
            "mac"
        } else {
            "linux"
        }
    }

    async fn get_download_url_tuna(
        &self,
        version: i32,
        java_type: JavaType,
    ) -> CoreResult<String> {
        // 映射到 Adoptium 的版本名
        let feature_version = if version <= 8 { 8 } else { version };

        // 识别 arch
        let arch = if cfg!(target_arch = "x86_64") {
            "x64"
        } else if cfg!(target_arch = "aarch64") {
            "aarch64"
        } else {
            "x86"
        };

        // 识别 os
        let os = if cfg!(target_os = "windows") {
            "windows"
        } else if cfg!(target_os = "macos") {
            "mac"
        } else {
            "linux"
        };

        // 镜像源 URL（与 py_fallback 一致: {version}/{type}/{arch}/{platform}）
        let page_url = format!(
            "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/{}/{}/{}/{}",
            feature_version,
            java_type.as_str(),
            arch,
            os
        );

        log::info!("获取 Java 下载列表: {}", page_url);

        // 获取页面 HTML
        let html = self.client.get_text(&page_url).await?;
        let document = Html::parse_document(&html);
        let link_selector = Selector::parse("a").map_err(|e| CoreError::Xml(e.to_string()))?;

        // 查找 MSI (Windows) 或 tar.gz (Linux/macOS) 链接
        let extension = if cfg!(target_os = "windows") {
            ".msi"
        } else if cfg!(target_os = "macos") {
            ".tar.gz"
        } else {
            ".tar.gz"
        };

        for element in document.select(&link_selector) {
            if let Some(href) = element.value().attr("href") {
                let url_lower = href.to_lowercase();
                let is_correct_type = if java_type == JavaType::Jre {
                    url_lower.contains("jre")
                } else {
                    url_lower.contains("jdk")
                };

                if is_correct_type && url_lower.ends_with(extension) {
                    return Ok(format!("{}/{}", page_url, href));
                }
            }
        }

        Err(CoreError::JavaNotFound(format!(
            "未找到 Java {} {} for {}/{}",
            version, java_type.as_str(), os, arch
        )))
    }

    /// 下载 Java 安装程序
    pub async fn download_java(
        &self,
        version: i32,
        java_type: JavaType,
        dest_dir: &Path,
    ) -> CoreResult<PathBuf> {
        let url = self.get_download_url(version, java_type, true).await?;

        let filename = url.rsplit('/').next().unwrap_or("java-installer.msi");
        let dest = dest_dir.join(filename);

        tokio::fs::create_dir_all(dest_dir).await?;

        log::info!("下载 Java {} {}: {}", version, java_type.as_str(), url);
        self.client
            .download_file(&url, &dest, None::<fn(u64, u64)>)
            .await?;

        Ok(dest)
    }
}

// ========================================================================
//  Java 版本选择器
// ========================================================================

/// 根据 Minecraft 版本选择合适的 Java 版本
pub fn select_java_for_minecraft(
    mc_version: &str,
    version_json: &VersionJson,
    javas: &[JavaInstallation],
) -> CoreResult<JavaInstallation> {
    let required_java = version_json
        .java_version
        .as_ref()
        .map(|jv| jv.major_version)
        .unwrap_or(8); // 默认为 Java 8

    // 找到满足最低要求的最新 Java
    javas
        .iter()
        .filter(|j| j.major_version >= required_java)
        .min_by_key(|j| j.major_version - required_java)
        .cloned()
        .ok_or_else(|| {
            CoreError::JavaNotFound(format!(
                "需要 Java {} 或更高版本运行 Minecraft {}，但未找到合适的 Java",
                required_java, mc_version
            ))
        })
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_version_java8() {
        let output = r#"openjdk version "1.8.0_462" 2025-01-21"#;
        let (major, full) = JavaDetector::parse_version_output(output).unwrap();
        assert_eq!(major, 8);
        assert_eq!(full, "1.8.0_462");
    }

    #[test]
    fn test_parse_version_java17() {
        let output = r#"openjdk version "17.0.12" 2024-07-16 LTS"#;
        let (major, full) = JavaDetector::parse_version_output(output).unwrap();
        assert_eq!(major, 17);
        assert_eq!(full, "17.0.12");
    }

    #[test]
    fn test_parse_version_java21() {
        let output = r#"openjdk version "21.0.2" 2025-01-21"#;
        let (major, full) = JavaDetector::parse_version_output(output).unwrap();
        assert_eq!(major, 21);
        assert_eq!(full, "21.0.2");
    }

    #[test]
    fn test_select_java_for_minecraft() {
        let javas = vec![
            JavaInstallation {
                path: PathBuf::from("/usr/lib/jvm/java-8"),
                major_version: 8,
                full_version: "1.8.0_462".into(),
                is_jre: false,
            },
            JavaInstallation {
                path: PathBuf::from("/usr/lib/jvm/java-17"),
                major_version: 17,
                full_version: "17.0.12".into(),
                is_jre: false,
            },
            JavaInstallation {
                path: PathBuf::from("/usr/lib/jvm/java-21"),
                major_version: 21,
                full_version: "21.0.2".into(),
                is_jre: false,
            },
        ];

        // Minecraft 1.20+ 需要 Java 17
        let vj = VersionJson {
            java_version: Some(JavaVersion {
                major_version: 17,
                ..Default::default()
            }),
            ..default_vj()
        };

        let selected = select_java_for_minecraft("1.20", &vj, &javas).unwrap();
        assert_eq!(selected.major_version, 17);
    }

    fn default_vj() -> VersionJson {
        VersionJson {
            id: String::new(),
            inherits_from: None,
            main_class: "net.minecraft.client.main.Main".into(),
            libraries: vec![],
            assets: None,
            asset_index: None,
            arguments: None,
            minecraft_arguments: None,
            java_version: None,
            downloads: None,
            release_time: None,
            time: None,
            minimum_launcher_version: None,
            logging: None,
        }
    }
}
