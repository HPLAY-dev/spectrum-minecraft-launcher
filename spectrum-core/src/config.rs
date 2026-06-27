//! # 配置管理
//!
//! 负责加载和保存启动器配置。
//!
//! 对应原 Python: `config.py`

use crate::types::*;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// 启动器配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LauncherConfig {
    /// Minecraft 根目录
    pub minecraft_dir: String,
    /// 选择的 Java 路径
    pub java_path: String,
    /// Xmx 内存上限
    pub xmx: String,
    /// Xms 内存下限
    pub xms: String,
    /// 窗口宽度
    pub window_width: u32,
    /// 窗口高度
    pub window_height: u32,
    /// 使用 BMCLAPI 镜像
    pub use_bmclapi: bool,
    /// 显示快照版本
    pub show_snapshot: bool,
    /// 显示旧版 Alpha
    pub show_old_alpha: bool,
    /// 显示旧版 Beta
    pub show_old_beta: bool,
    /// 额外 JVM 参数
    pub extra_jvm_args: String,
    /// 额外游戏参数
    pub extra_game_args: String,
    /// 已保存的账户
    pub accounts: Vec<Account>,
    /// 当前选定账户索引
    pub selected_account: usize,
    /// 最近使用的实例
    pub last_instance: Option<String>,
    /// 自定义服务器 IP
    pub server_ip: Option<String>,
    /// 自定义服务器端口
    pub server_port: Option<u16>,
    /// 主题 (light/dark)
    pub theme: String,
    /// 语言
    pub language: String,
}

impl Default for LauncherConfig {
    fn default() -> Self {
        Self {
            minecraft_dir: if cfg!(target_os = "windows") {
                let appdata = std::env::var("APPDATA").unwrap_or_else(|_| {
                    std::env::var("USERPROFILE").unwrap_or_else(|_| ".".into())
                });
                format!("{}\\SpectrumLauncher", appdata)
            } else if cfg!(target_os = "macos") {
                let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".into());
                format!("{}/Library/Application Support/SpectrumLauncher", home)
            } else {
                let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".into());
                format!("{}/.spectrum_launcher", home)
            },
            java_path: String::new(),
            xmx: "2048M".into(),
            xms: "1024M".into(),
            window_width: 854,
            window_height: 480,
            use_bmclapi: true,
            show_snapshot: false,
            show_old_alpha: false,
            show_old_beta: false,
            extra_jvm_args: String::new(),
            extra_game_args: String::new(),
            accounts: Vec::new(),
            selected_account: 0,
            last_instance: None,
            server_ip: None,
            server_port: None,
            theme: "dark".into(),
            language: "zh-CN".into(),
        }
    }
}

impl LauncherConfig {
    /// 从文件加载配置
    pub fn load(path: &Path) -> CoreResult<Self> {
        if !path.exists() {
            log::info!("配置文件不存在, 使用默认配置");
            return Ok(Self::default());
        }

        let content = std::fs::read_to_string(path)
            .map_err(|e| CoreError::Io(e))?;
        let config: LauncherConfig = serde_json::from_str(&content)
            .map_err(|e| CoreError::Json(e))?;
        log::info!("配置已加载: {}", path.display());
        Ok(config)
    }

    /// 保存配置到文件
    pub fn save(&self, path: &Path) -> CoreResult<()> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| CoreError::Io(e))?;
        }

        let content = serde_json::to_string_pretty(self)
            .map_err(|e| CoreError::Json(e))?;
        std::fs::write(path, content)
            .map_err(|e| CoreError::Io(e))?;
        log::info!("配置已保存: {}", path.display());
        Ok(())
    }

    /// 获取子目录路径
    fn sub_dir(&self, name: &str) -> PathBuf {
        PathBuf::from(&self.minecraft_dir).join(name)
    }

    /// 版本目录
    pub fn versions_dir(&self) -> PathBuf {
        self.sub_dir("versions")
    }

    /// 资源目录
    pub fn assets_dir(&self) -> PathBuf {
        self.sub_dir("assets")
    }

    /// 库目录
    pub fn libraries_dir(&self) -> PathBuf {
        self.sub_dir("libraries")
    }

    /// 原生库目录 (natives)
    pub fn natives_dir(&self) -> PathBuf {
        self.sub_dir("natives")
    }

    /// 下载缓存目录
    pub fn cache_dir(&self) -> PathBuf {
        self.sub_dir("cache")
    }

    /// 日志目录
    pub fn logs_dir(&self) -> PathBuf {
        self.sub_dir("logs")
    }

    /// 实例目录
    pub fn instance_dir(&self, name: &str) -> PathBuf {
        self.versions_dir().join(name)
    }

    /// 获取当前选中的账户
    pub fn current_account(&self) -> Option<&Account> {
        self.accounts.get(self.selected_account)
    }

    /// 添加账户
    pub fn add_account(&mut self, account: Account) {
        self.accounts.push(account);
    }

    /// 移除账户
    pub fn remove_account(&mut self, index: usize) {
        if index < self.accounts.len() {
            self.accounts.remove(index);
            if self.selected_account >= self.accounts.len() && !self.accounts.is_empty() {
                self.selected_account = self.accounts.len() - 1;
            }
        }
    }
}
