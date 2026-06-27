//! 从 client.jar 内嵌的 `version.json` 读取 Minecraft 版本（18w47b+）

use serde::Deserialize;
use std::io::Read;
use std::path::{Path, PathBuf};

#[derive(Debug, Deserialize)]
struct EmbeddedVersionJson {
    id: String,
    #[serde(default)]
    name: Option<String>,
}

/// 定位实例目录中的 client jar
pub fn find_instance_client_jar(
    instance_dir: &Path,
    instance_name: &str,
    version_id: &str,
) -> Option<PathBuf> {
    for candidate in [
        instance_dir.join(format!("{instance_name}.jar")),
        instance_dir.join(format!("{version_id}.jar")),
    ] {
        if candidate.is_file() {
            return Some(candidate);
        }
    }

    let mut jars: Vec<PathBuf> = std::fs::read_dir(instance_dir)
        .ok()?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.extension().is_some_and(|ext| ext == "jar"))
        .collect();
    if jars.len() == 1 {
        return jars.pop();
    }
    None
}

/// 从 jar 根目录的 `version.json` 读取 MC 版本 id
pub fn read_mc_version_from_jar(jar_path: &Path) -> Option<String> {
    let file = std::fs::File::open(jar_path).ok()?;
    let mut archive = zip::ZipArchive::new(file).ok()?;
    let mut entry = archive.by_name("version.json").ok()?;
    let mut content = String::new();
    entry.read_to_string(&mut content).ok()?;
    parse_embedded_version_json(&content)
}

fn parse_embedded_version_json(content: &str) -> Option<String> {
    let v: EmbeddedVersionJson = serde_json::from_str(content).ok()?;
    let id = v.id.trim();
    if !id.is_empty() {
        return Some(id.to_string());
    }
    v.name
        .as_ref()
        .map(|s| s.trim())
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
}

/// 从实例目录中的 client jar 读取 MC 版本
pub fn read_mc_version_from_instance(
    instance_dir: &Path,
    instance_name: &str,
    version_id: &str,
) -> Option<String> {
    let jar = find_instance_client_jar(instance_dir, instance_name, version_id)?;
    read_mc_version_from_jar(&jar)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    fn write_test_jar(dir: &Path, version_id: &str) -> PathBuf {
        let jar = dir.join("client.jar");
        let file = std::fs::File::create(&jar).unwrap();
        let mut zip = zip::ZipWriter::new(file);
        let opts =
            zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored);
        zip.start_file("version.json", opts).unwrap();
        write!(
            zip,
            r#"{{"id":"{version_id}","name":"{version_id}"}}"#
        )
        .unwrap();
        zip.finish().unwrap();
        jar
    }

    #[test]
    fn reads_version_json_from_jar() {
        let dir = std::env::temp_dir().join(format!("spectrum_jar_test_{}", std::process::id()));
        let _ = std::fs::create_dir_all(&dir);
        let jar = write_test_jar(&dir, "1.21.1");
        assert_eq!(
            read_mc_version_from_jar(&jar).as_deref(),
            Some("1.21.1")
        );
        let _ = std::fs::remove_dir_all(&dir);
    }
}
