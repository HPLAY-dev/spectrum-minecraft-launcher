//! # ModLoader 安装器
//!
//! 所有 ModLoader 安装的统一入口。
//! 支持 Fabric, Forge, NeoForge, OptiFine, LabyMod。

pub mod fabric;
pub mod forge;
pub mod neoforge;
pub mod optifine;
pub mod labymod;

use crate::http_client::HttpClient;
use crate::types::*;
use std::path::Path;

/// ModLoader 安装器 trait
#[async_trait::async_trait]
pub trait ModLoaderInstaller: Send + Sync {
    /// 获取 ModLoader 名称
    fn name(&self) -> &'static str;

    /// 获取支持的 Minecraft 版本列表
    async fn get_supported_versions(&self) -> CoreResult<Vec<String>>;

    /// 获取指定版本的 ModLoader 版本列表
    async fn get_loader_versions(&self, mc_version: &str) -> CoreResult<Vec<String>>;

    /// 安装 ModLoader 到指定实例
    async fn install(
        &self,
        mc_version: &str,
        loader_version: Option<&str>,
        instance_dir: &Path,
        minecraft_dir: &Path,
    ) -> CoreResult<VersionJson>;
}

/// ModLoader 分发器 — 根据类型选择对应的安装器
pub fn get_installer(client: HttpClient, loader: ModLoader) -> Option<Box<dyn ModLoaderInstaller>> {
    match loader {
        ModLoader::Fabric => Some(Box::new(fabric::FabricInstaller::new(client))),
        ModLoader::Forge => Some(Box::new(forge::ForgeInstaller::new(client))),
        ModLoader::NeoForge => Some(Box::new(neoforge::NeoForgeInstaller::new(client))),
        ModLoader::OptiFine => Some(Box::new(optifine::OptiFineInstaller::new(client))),
        ModLoader::LabyMod => Some(Box::new(labymod::LabyModInstaller::new(client))),
        ModLoader::Vanilla => None,
    }
}
