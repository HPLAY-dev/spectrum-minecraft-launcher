//! # Spectrum Launcher Core
//!
//! Rust 异步核心库 — 负责所有多线程 / 网络 / 高性能任务。
//! 提供 C FFI 供 C++ Qt6 GUI 调用。

pub mod types;
pub mod http_client;
pub mod manifest;
pub mod download;
pub mod oauth;
pub mod java;
pub mod launcher;
pub mod manager;
pub mod config;
pub mod modloader;
pub mod natives;
pub mod ffi;

#[cfg(feature = "python")]
mod python;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn _spectrum_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    python::init_module(m)
}

// 再导出核心类型与常用模块
pub use types::*;
pub use http_client::HttpClient;
pub use download::{DownloadEngine, AutoDownloadOptions};
pub use manifest::{ManifestManager, VersionJsonManager, AssetIndexManager};
pub use launcher::LaunchCommandBuilder;
pub use manager::InstanceManager;
pub use oauth::OAuthClient;
pub use java::{JavaDetector, JavaDownloader, select_java_for_minecraft};
pub use config::LauncherConfig;
pub use natives::{natives_dir, flatten_natives_dir};

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
