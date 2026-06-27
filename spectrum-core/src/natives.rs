//! # Natives 原生库处理
//!
//! 下载、解压 LWJGL 等 native JAR，并扁平化到 `{instance}-natives/` 目录。
//! 对应原 Python: `download_funcs.download_native_library` + natives 后处理

use crate::types::*;
use std::path::{Path, PathBuf};

/// 实例 natives 目录: `versions/{instance}/{instance}-natives`
pub fn natives_dir(instance_dir: &Path, instance_name: &str) -> PathBuf {
    instance_dir.join(format!("{instance_name}-natives"))
}

/// 从 classifiers 中解析当前平台的 native artifact
pub fn pick_native_artifact(
    classifiers: &std::collections::HashMap<String, ArtifactDownload>,
) -> Option<&ArtifactDownload> {
    for key in native_classifier_keys() {
        if let Some(artifact) = classifiers.get(&key) {
            return Some(artifact);
        }
    }
    None
}

/// 解压 natives ZIP 到目标目录，按 extract.exclude 跳过条目
pub async fn extract_natives_archive(
    archive_path: &Path,
    dest_dir: &Path,
    exclude: &[String],
) -> CoreResult<()> {
    tokio::fs::create_dir_all(dest_dir).await?;

    let archive_path = archive_path.to_path_buf();
    let dest_dir = dest_dir.to_path_buf();
    let exclude: Vec<String> = exclude.to_vec();

    tokio::task::spawn_blocking(move || {
        let file = std::fs::File::open(&archive_path)?;
        let mut archive = zip::ZipArchive::new(file)?;

        for i in 0..archive.len() {
            let mut entry = archive.by_index(i)?;
            let name = entry.name().to_string();

            if exclude.iter().any(|e| name.contains(e)) {
                continue;
            }

            let out_path = dest_dir.join(&name);
            if name.ends_with('/') {
                std::fs::create_dir_all(&out_path)?;
                continue;
            }

            if let Some(parent) = out_path.parent() {
                std::fs::create_dir_all(parent)?;
            }

            let mut out_file = std::fs::File::create(&out_path)?;
            std::io::copy(&mut entry, &mut out_file)?;
        }
        Ok::<(), CoreError>(())
    })
    .await
    .map_err(|e| CoreError::Unknown(format!("natives 解压任务失败: {e}")))??;

    Ok(())
}

/// 将子目录中的 .dll/.so/.dylib 提升到 natives 根目录，并清理 OS 子目录与 META-INF
pub async fn flatten_natives_dir(natives_dir: &Path) -> CoreResult<()> {
    let natives_dir = natives_dir.to_path_buf();
    tokio::task::spawn_blocking(move || flatten_natives_dir_sync(&natives_dir))
        .await
        .map_err(|e| CoreError::Unknown(format!("natives 扁平化任务失败: {e}")))??;
    Ok(())
}

fn flatten_natives_dir_sync(natives_dir: &Path) -> CoreResult<()> {
    if !natives_dir.exists() {
        return Ok(());
    }

    let mut native_files: Vec<PathBuf> = Vec::new();
    collect_native_files(natives_dir, &mut native_files)?;

    for src in native_files {
        let file_name = src.file_name().unwrap();
        let dest = natives_dir.join(file_name);
        if src != dest {
            std::fs::copy(&src, &dest)?;
        }
    }

    // 删除 OS 子目录与 META-INF
    let os_subdir = natives_dir.join(native_os());
    if os_subdir.exists() {
        let _ = std::fs::remove_dir_all(&os_subdir);
    }
    let meta = natives_dir.join("META-INF");
    if meta.exists() {
        let _ = std::fs::remove_dir_all(&meta);
    }

    Ok(())
}

fn collect_native_files(dir: &Path, out: &mut Vec<PathBuf>) -> CoreResult<()> {
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_native_files(&path, out)?;
        } else if is_native_lib(&path) {
            out.push(path);
        }
    }
    Ok(())
}

fn is_native_lib(path: &Path) -> bool {
    path.extension()
        .and_then(|e| e.to_str())
        .map(|e| matches!(e, "dll" | "so" | "dylib"))
        .unwrap_or(false)
}
