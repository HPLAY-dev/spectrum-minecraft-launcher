//! # 实例管理
//!
//! 负责管理已下载的 Minecraft 实例:
//! - 列出所有已安装的实例
//! - 删除实例
//! - 获取实例信息
//! - 复制/重命名实例
//!
//! 对应原 Python: `manager.py`

use crate::types::*;
use std::path::{Path, PathBuf};

/// 实例信息
#[derive(Debug, Clone)]
pub struct InstanceInfo {
    pub name: String,
    pub mc_version: String,
    pub modloader: ModLoader,
    pub path: PathBuf,
    pub game_jar: PathBuf,
    pub version_json: VersionJson,
    pub size: u64,
    pub last_played: Option<String>,
}

/// 实例管理器
pub struct InstanceManager {
    minecraft_dir: PathBuf,
}

impl InstanceManager {
    pub fn new(minecraft_dir: PathBuf) -> Self {
        Self { minecraft_dir }
    }

    /// 设置 Minecraft 目录
    pub fn set_minecraft_dir(&mut self, dir: PathBuf) {
        self.minecraft_dir = dir;
    }

    /// 获取 Minecraft 目录
    pub fn minecraft_dir(&self) -> &Path {
        &self.minecraft_dir
    }

    /// 列出所有已安装的实例
    pub fn list_instances(&self) -> CoreResult<Vec<String>> {
        let versions_dir = self.minecraft_dir.join("versions");
        if !versions_dir.exists() {
            return Ok(Vec::new());
        }

        let mut instances = Vec::new();
        let entries = std::fs::read_dir(&versions_dir)
            .map_err(|e| CoreError::Io(e))?;

        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                if let Some(name) = path.file_name() {
                    instances.push(name.to_string_lossy().to_string());
                }
            }
        }

        instances.sort();
        Ok(instances)
    }

    /// 获取实例详细信息
    pub fn get_instance_info(&self, name: &str) -> CoreResult<InstanceInfo> {
        let instance_dir = self.minecraft_dir.join("versions").join(name);
        if !instance_dir.exists() {
            return Err(CoreError::VersionNotFound(format!(
                "实例 '{}' 不存在", name
            )));
        }

        // 查找 version.json
        let json_path = instance_dir.join(format!("{}.json", name));
        let json_path = if json_path.exists() {
            json_path
        } else {
            // 回退: 找第一个 *.json
            let json_files: Vec<_> = std::fs::read_dir(&instance_dir)
                .map_err(|e| CoreError::Io(e))?
                .filter_map(|e| e.ok())
                .filter(|e| e.path().extension().map_or(false, |ext| ext == "json"))
                .collect();

            if json_files.is_empty() {
                return Err(CoreError::VersionNotFound(format!(
                    "实例 '{}' 缺少 version.json", name
                )));
            }
            json_files[0].path()
        };

        // 解析 version.json
        let content = std::fs::read_to_string(&json_path)
            .map_err(|e| CoreError::Io(e))?;
        let vj: VersionJson = serde_json::from_str(&content)?;

        // 查找客户端 JAR
        let jar_path = instance_dir.join(format!("{}.jar", vj.id));
        let jar_path = if jar_path.exists() { jar_path }
        else {
            // 回退: 找 *.jar
            instance_dir.join(format!("{}.jar", name))
        };

        // 计算大小
        let size = Self::dir_size(&instance_dir);

        let modloader = crate::modloader::instance_json::detect_modloader(name, &vj);

        Ok(InstanceInfo {
            name: name.to_string(),
            mc_version: crate::modloader::instance_json::guess_mc_version_in_dir(
                name,
                &vj,
                Some(&instance_dir),
            ),
            modloader,
            path: instance_dir,
            game_jar: jar_path,
            version_json: vj,
            size,
            last_played: None, // 留由外部设置
        })
    }

    /// 删除实例
    pub fn delete_instance(&self, name: &str) -> CoreResult<()> {
        let instance_dir = self.minecraft_dir.join("versions").join(name);
        if !instance_dir.exists() {
            return Err(CoreError::VersionNotFound(format!(
                "实例 '{}' 不存在", name
            )));
        }
        std::fs::remove_dir_all(&instance_dir)
            .map_err(|e| CoreError::Io(e))?;
        log::info!("实例已删除: {}", name);
        Ok(())
    }

    /// 重命名实例
    pub fn rename_instance(&self, old_name: &str, new_name: &str) -> CoreResult<()> {
        let old_path = self.minecraft_dir.join("versions").join(old_name);
        let new_path = self.minecraft_dir.join("versions").join(new_name);

        if !old_path.exists() {
            return Err(CoreError::VersionNotFound(format!(
                "实例 '{}' 不存在", old_name
            )));
        }
        if new_path.exists() {
            return Err(CoreError::InvalidArgument(format!(
                "实例 '{}' 已存在", new_name
            )));
        }

        std::fs::rename(&old_path, &new_path)
            .map_err(|e| CoreError::Io(e))?;

        // 更新 JSON 文件中的实例名称
        let json_path = new_path.join(format!("{}.json", new_name));
        if !json_path.exists() {
            // 重命名旧的 JSON
            let old_json = new_path.join(format!("{}.json", old_name));
            if old_json.exists() {
                std::fs::rename(&old_json, &json_path)
                    .map_err(|e| CoreError::Io(e))?;
            }
        }

        log::info!("实例已重命名: {} → {}", old_name, new_name);
        Ok(())
    }

    /// 检查实例是否存在
    pub fn instance_exists(&self, name: &str) -> bool {
        self.minecraft_dir.join("versions").join(name).exists()
    }

    // ====================================================================
    //  实例内容管理 — 对应 Python manager.py
    // ====================================================================

    fn instance_path(&self, instance: &str, sub: &str) -> PathBuf {
        self.minecraft_dir.join("versions").join(instance).join(sub)
    }

    fn list_dir_names(&self, dir: &Path) -> CoreResult<Vec<String>> {
        if !dir.exists() {
            return Ok(Vec::new());
        }
        let mut names = Vec::new();
        for entry in std::fs::read_dir(dir).map_err(CoreError::Io)? {
            let entry = entry.map_err(CoreError::Io)?;
            if entry.path().is_dir() || entry.path().is_file() {
                if let Some(name) = entry.file_name().to_str() {
                    names.push(name.to_string());
                }
            }
        }
        names.sort();
        Ok(names)
    }

    pub fn get_saves(&self, instance: &str) -> CoreResult<Vec<String>> {
        self.list_dir_names(&self.instance_path(instance, "saves"))
    }

    pub fn get_mods(&self, instance: &str) -> CoreResult<Vec<String>> {
        self.list_dir_names(&self.instance_path(instance, "mods"))
    }

    pub fn get_resourcepacks(&self, instance: &str) -> CoreResult<Vec<String>> {
        self.list_dir_names(&self.instance_path(instance, "resourcepacks"))
    }

    pub fn get_shaderpacks(&self, instance: &str) -> CoreResult<Vec<String>> {
        self.list_dir_names(&self.instance_path(instance, "shaderpacks"))
    }

    pub fn remove_save(&self, instance: &str, name: &str) -> CoreResult<()> {
        let path = self.instance_path(instance, "saves").join(name);
        if path.is_dir() {
            std::fs::remove_dir_all(&path).map_err(CoreError::Io)?;
        } else if path.exists() {
            std::fs::remove_file(&path).map_err(CoreError::Io)?;
        }
        Ok(())
    }

    pub fn remove_mod(&self, instance: &str, name: &str) -> CoreResult<()> {
        let path = self.instance_path(instance, "mods").join(name);
        if path.is_dir() {
            std::fs::remove_dir_all(&path).map_err(CoreError::Io)?;
        } else if path.is_file() {
            std::fs::remove_file(&path).map_err(CoreError::Io)?;
        }
        Ok(())
    }

    pub fn remove_resourcepack(&self, instance: &str, name: &str) -> CoreResult<()> {
        let path = self.instance_path(instance, "resourcepacks").join(name);
        if path.exists() {
            std::fs::remove_dir_all(&path).map_err(CoreError::Io)?;
        }
        Ok(())
    }

    pub fn remove_shaderpack(&self, instance: &str, name: &str) -> CoreResult<()> {
        let path = self.instance_path(instance, "shaderpacks").join(name);
        if path.exists() {
            std::fs::remove_dir_all(&path).map_err(CoreError::Io)?;
        }
        Ok(())
    }

    // ====================================================================
    //  辅助方法
    // ====================================================================

    /// 检测 ModLoader 类型
    fn detect_modloader(vj: &VersionJson) -> ModLoader {
        let main_class = vj.main_class.to_lowercase();
        let libraries_names: Vec<&str> = vj.libraries.iter()
            .map(|l| l.name.as_str())
            .collect();
        let libs_concat = libraries_names.join(" ").to_lowercase();

        if libs_concat.contains("net.minecraftforge") || libs_concat.contains("forge") {
            ModLoader::Forge
        } else if libs_concat.contains("net.fabricmc") || libs_concat.contains("fabric") {
            ModLoader::Fabric
        } else if libs_concat.contains("net.neoforged") || libs_concat.contains("neoforge") {
            ModLoader::NeoForge
        } else if libs_concat.contains("optifine") || libs_concat.contains("optifine") {
            ModLoader::OptiFine
        } else if libs_concat.contains("labymod") || main_class.contains("labymod") {
            ModLoader::LabyMod
        } else {
            ModLoader::Vanilla
        }
    }

    /// 计算目录大小
    fn dir_size(path: &Path) -> u64 {
        let mut total = 0u64;
        if let Ok(entries) = std::fs::read_dir(path) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_file() {
                    if let Ok(metadata) = std::fs::metadata(&path) {
                        total += metadata.len();
                    }
                } else if path.is_dir() {
                    total += Self::dir_size(&path);
                }
            }
        }
        total
    }
}
