//! # Minecraft 启动命令构建器
//!
//! 组装 Java 命令行启动 Minecraft — 等价 Python `launcher_funcs.launch` + `get_jvm_args`。

use crate::manifest::VersionJsonManager;
use crate::natives::natives_dir;
use crate::types::*;

/// 启动命令构建器
#[derive(Debug, Clone)]
pub struct LaunchCommandBuilder;

impl LaunchCommandBuilder {
    /// 从实例目录加载并合并 version JSON
    pub async fn load_instance_version_json(
        json_path: &std::path::Path,
        client: crate::http_client::HttpClient,
    ) -> CoreResult<VersionJson> {
        let mut mgr = VersionJsonManager::new(client.clone());
        let mut manifest_mgr = crate::manifest::ManifestManager::new(client);
        mgr.resolve_instance_json(json_path, &mut manifest_mgr).await
    }

    /// 构建完整启动命令
    pub fn build_command(config: &LaunchConfig, version_json: &VersionJson) -> CoreResult<Vec<String>> {
        let mut args: Vec<String> = Vec::new();

        args.push(config.java_path.clone());

        if !config.xmx.is_empty() {
            args.push(format!("-Xmx{}", config.xmx));
        }
        if !config.xms.is_empty() {
            args.push(format!("-Xms{}", config.xms));
        }

        // JVM 优化参数
        args.push("-XX:+UseG1GC".into());
        args.push("-XX:-UseAdaptiveSizePolicy".into());
        args.push("-XX:-OmitStackTraceInFastThrow".into());
        args.push("-Dfml.ignoreInvalidMinecraftCertificates=True".into());
        args.push("-Dfml.ignorePatchDiscrepancies=True".into());
        args.push("-Dlog4j2.formatMsgNoLookups=true".into());

        // natives 路径
        let natives = natives_dir(&config.game_directory, &config.instance_name);
        args.push(format!(
            "-Djava.library.path={}",
            natives.to_string_lossy()
        ));

        // version JSON 中的 JVM 参数模板（NeoForge 等在此注入 -cp ${classpath}）
        let classpath = Self::build_classpath(config, version_json)?;
        let jvm_has_classpath = Self::jvm_arguments_include_classpath(version_json);
        Self::append_jvm_arguments(&mut args, version_json, config, &classpath);

        if !config.extra_jvm_args.is_empty() {
            for extra in config.extra_jvm_args.split_whitespace() {
                args.push(extra.to_string());
            }
        }

        if !Self::uses_module_path(version_json) && !jvm_has_classpath {
            args.push("-cp".into());
            args.push(classpath);
        }

        if let Some(ref wrapper) = config.javawrapper {
            if !Self::should_skip_javawrapper(version_json) {
                args.push("-jar".into());
                args.push(wrapper.to_string_lossy().to_string());
            }
        }

        args.push(version_json.main_class.clone());

        let mut game_args = Self::build_game_args(config, version_json)?;
        game_args = Self::sanitize_game_args(game_args);
        if let (Some(ref ip), Some(port)) = (&config.server_ip, config.server_port) {
            game_args.push("--server".into());
            game_args.push(ip.clone());
            game_args.push("--port".into());
            game_args.push(port.to_string());
        }
        args.extend(game_args);

        Ok(args)
    }

    /// 追加 version JSON 中的 JVM 参数，并展开 ${classpath}
    fn append_jvm_arguments(
        args: &mut Vec<String>,
        vj: &VersionJson,
        config: &LaunchConfig,
        classpath: &str,
    ) {
        let Some(ref arguments) = vj.arguments else {
            return;
        };
        if arguments.jvm.is_empty() {
            return;
        }

        for arg in &arguments.jvm {
            match arg {
                Argument::Value(s) => {
                    let v = Self::expand_jvm_arg(s, config, vj, classpath);
                    if Self::is_valid_launch_arg(&v) {
                        args.push(v);
                    }
                }
                Argument::Rules { rules, value } if rules_compatible(rules) => {
                    let values = match value {
                        ArgumentValue::Single(s) => vec![Self::expand_jvm_arg(s, config, vj, classpath)],
                        ArgumentValue::Multi(v) => v
                            .iter()
                            .map(|s| Self::expand_jvm_arg(s, config, vj, classpath))
                            .collect(),
                    };
                    for v in values {
                        if Self::is_valid_launch_arg(&v) {
                            args.push(v);
                        }
                    }
                }
                Argument::Rules { .. } => {}
            }
        }
    }

    fn expand_jvm_arg(
        template: &str,
        config: &LaunchConfig,
        version_json: &VersionJson,
        classpath: &str,
    ) -> String {
        Self::replace_tokens(template, config, version_json).replace("${classpath}", classpath)
    }

    fn jvm_arguments_include_classpath(vj: &VersionJson) -> bool {
        let Some(ref arguments) = vj.arguments else {
            return false;
        };
        arguments.jvm.iter().any(|arg| match arg {
            Argument::Value(s) => s.contains("classpath"),
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => s.contains("classpath"),
                ArgumentValue::Multi(v) => v.iter().any(|s| s.contains("classpath")),
            },
        })
    }

    /// NeoForge 使用 `-p` 模块路径；`-cp` 由 JSON 模板中的 ${classpath} 提供。
    fn uses_module_path(vj: &VersionJson) -> bool {
        if vj.main_class.to_lowercase().contains("bootstraplauncher") {
            return true;
        }
        let Some(ref arguments) = vj.arguments else {
            return false;
        };
        arguments.jvm.iter().any(|arg| match arg {
            Argument::Value(s) => s == "-p",
            Argument::Rules { value, .. } => match value {
                ArgumentValue::Single(s) => s == "-p",
                ArgumentValue::Multi(v) => v.iter().any(|s| s == "-p"),
            },
        })
    }

    /// BootstrapLauncher 等模组入口不能经 JavaWrapper 间接启动。
    fn should_skip_javawrapper(vj: &VersionJson) -> bool {
        let mc = vj.main_class.to_lowercase();
        mc.contains("bootstraplauncher")
            || mc.contains("knotclient")
            || mc.contains("modlauncher")
            || mc.contains("launchwrapper")
    }

    fn build_classpath(config: &LaunchConfig, version_json: &VersionJson) -> CoreResult<String> {
        let mut paths = Vec::new();
        let mut seen = std::collections::HashSet::new();
        let module_path = Self::module_path_entries(version_json, config);
        let skip_client_jar = version_json
            .main_class
            .contains("BootstrapLauncher");
        let mut client_jar: Option<std::path::PathBuf> = None;

        let mut push_path = |path: std::path::PathBuf| {
            if !path.exists() || Self::is_native_artifact(&path) {
                return;
            }
            if Self::is_on_module_path(&path, &module_path) {
                return;
            }
            let key = Self::normalize_path_key(&path);
            if seen.insert(key) {
                paths.push(path);
            }
        };

        let jar_candidates = [
            config.game_directory.join(format!("{}.jar", config.instance_name)),
            config
                .game_directory
                .join(format!("{}.jar", version_json.id)),
        ];
        for jar in jar_candidates {
            if jar.exists() {
                client_jar = Some(jar);
                break;
            }
        }

        for lib in &version_json.libraries {
            if !Self::is_library_compatible(lib) || Self::is_native_library_name(&lib.name) {
                continue;
            }

            if let Some(ref dl) = lib.downloads {
                if let Some(ref artifact) = dl.artifact {
                    push_path(config.libraries_directory.join(&artifact.path));
                    continue;
                }
            }

            if let Ok(maven_path) = maven_to_path(&lib.name) {
                push_path(config.libraries_directory.join(&maven_path));
            }
        }

        // NeoForge 由 production client provider 加载 patched client，原版 jar 仅由 ignoreList 引用
        if !skip_client_jar {
            if let Some(jar) = client_jar {
                push_path(jar);
            }
        }

        let sep = if cfg!(target_os = "windows") { ";" } else { ":" };
        Ok(paths
            .iter()
            .map(|p| p.to_string_lossy().to_string())
            .collect::<Vec<_>>()
            .join(sep))
    }

    fn module_path_entries(
        vj: &VersionJson,
        config: &LaunchConfig,
    ) -> std::collections::HashSet<String> {
        let mut entries = std::collections::HashSet::new();
        let flat = Self::flatten_jvm_arguments(vj);
        if flat.is_empty() {
            return entries;
        }
        let sep = if cfg!(target_os = "windows") { ";" } else { ":" };

        let mut i = 0;
        while i < flat.len() {
            if flat[i] == "-p" && i + 1 < flat.len() {
                let expanded = Self::replace_tokens(&flat[i + 1], config, vj);
                for part in expanded.split(sep) {
                    let key = Self::normalize_path_key_str(part.trim());
                    if !key.is_empty() {
                        entries.insert(key);
                    }
                }
                i += 2;
            } else {
                i += 1;
            }
        }
        entries
    }

    fn flatten_jvm_arguments(vj: &VersionJson) -> Vec<String> {
        let Some(ref arguments) = vj.arguments else {
            return Vec::new();
        };
        let mut flat = Vec::new();
        for arg in &arguments.jvm {
            match arg {
                Argument::Value(s) => flat.push(s.clone()),
                Argument::Rules { rules, value } if rules_compatible(rules) => match value {
                    ArgumentValue::Single(s) => flat.push(s.clone()),
                    ArgumentValue::Multi(v) => flat.extend(v.iter().cloned()),
                },
                Argument::Rules { .. } => {}
            }
        }
        flat
    }

    fn normalize_path_key(path: &std::path::Path) -> String {
        Self::normalize_path_key_str(&path.to_string_lossy())
    }

    fn normalize_path_key_str(path: &str) -> String {
        path.to_ascii_lowercase().replace('\\', "/")
    }

    fn is_on_module_path(path: &std::path::Path, module_path: &std::collections::HashSet<String>) -> bool {
        let key = Self::normalize_path_key(path);
        if module_path.contains(&key) {
            return true;
        }
        // 兜底：按 jar 文件名匹配（防止路径分隔符差异导致漏过滤）
        path.file_name()
            .map(|n| module_path.iter().any(|mp| mp.ends_with(&Self::normalize_path_key_str(&n.to_string_lossy()))))
            .unwrap_or(false)
    }

    fn is_native_library_name(name: &str) -> bool {
        name.contains(":natives-") || name.contains(":natives_")
    }

    fn is_native_artifact(path: &std::path::Path) -> bool {
        path.file_name()
            .map(|n| n.to_string_lossy().contains("-natives-"))
            .unwrap_or(false)
    }

    fn build_game_args(config: &LaunchConfig, version_json: &VersionJson) -> CoreResult<Vec<String>> {
        let mut args = Vec::new();

        if let Some(ref arguments) = version_json.arguments {
            if !arguments.game.is_empty() {
                for arg in &arguments.game {
                    Self::process_argument_template(arg, config, version_json, &mut args);
                }
                if !config.extra_game_args.is_empty() {
                    args.extend(config.extra_game_args.split_whitespace().map(String::from));
                }
                return Ok(args);
            }
        }

        if let Some(ref mc_args) = version_json.minecraft_arguments {
            let processed = Self::replace_tokens(mc_args, config, version_json);
            args.extend(
                processed
                    .split_whitespace()
                    .map(String::from)
                    .filter(|s| Self::is_valid_launch_arg(s)),
            );
        } else {
            args.extend(Self::build_basic_game_args(config, version_json));
        }

        if !config.extra_game_args.is_empty() {
            args.extend(config.extra_game_args.split_whitespace().map(String::from));
        }

        Ok(args)
    }

    fn process_argument_template(
        arg: &Argument,
        config: &LaunchConfig,
        version_json: &VersionJson,
        out: &mut Vec<String>,
    ) {
        match arg {
            Argument::Value(s) => {
                let v = Self::replace_tokens(s, config, version_json);
                if Self::is_valid_launch_arg(&v) {
                    out.push(v);
                }
            }
            Argument::Rules { rules, value } if rules_compatible(rules) => match value {
                ArgumentValue::Single(s) => {
                    let v = Self::replace_tokens(s, config, version_json);
                    if Self::is_valid_launch_arg(&v) {
                        out.push(v);
                    }
                }
                ArgumentValue::Multi(v) => {
                    out.extend(
                        v.iter()
                            .map(|s| Self::replace_tokens(s, config, version_json))
                            .filter(|s| Self::is_valid_launch_arg(s)),
                    );
                }
            },
            Argument::Rules { .. } => {}
        }
    }

    fn asset_index_name(version_json: &VersionJson) -> String {
        version_json
            .asset_index
            .as_ref()
            .map(|a| a.id.clone())
            .or_else(|| version_json.assets.clone())
            .unwrap_or_else(|| "legacy".into())
    }

    fn replace_tokens(template: &str, config: &LaunchConfig, version_json: &VersionJson) -> String {
        let asset_index = Self::asset_index_name(version_json);
        template
            .replace("${auth_player_name}", &config.username)
            .replace("${version_name}", &config.instance_name)
            .replace("${game_directory}", &config.game_directory.to_string_lossy())
            .replace("${game_assets}", &config.assets_directory.to_string_lossy())
            .replace("${assets_root}", &config.assets_directory.to_string_lossy())
            .replace("${assets_index_name}", &asset_index)
            .replace("${auth_uuid}", &config.uuid)
            .replace("${auth_access_token}", &config.access_token)
            .replace("${user_type}", &config.user_type)
            .replace("${version_type}", &config.version_type)
            .replace("${resolution_width}", &config.width.to_string())
            .replace("${resolution_height}", &config.height.to_string())
            .replace("${natives_directory}", &config.natives_directory.to_string_lossy())
            .replace("${launcher_name}", "SerenaLauncher")
            .replace("${launcher_version}", env!("CARGO_PKG_VERSION"))
            .replace("${clientid}", "")
            .replace("${auth_xuid}", "")
            .replace("${quickPlayPath}", "")
            .replace("${quickPlaySingleplayer}", "")
            .replace("${quickPlayMultiplayer}", "")
            .replace("${quickPlayRealms}", "")
            .replace(
                "${classpath_separator}",
                if cfg!(target_os = "windows") { ";" } else { ":" },
            )
            .replace(
                "${library_directory}",
                &config.libraries_directory.to_string_lossy(),
            )
    }

    fn is_valid_launch_arg(value: &str) -> bool {
        !value.is_empty() && !value.contains("${")
    }

    /// 移除未替换的占位符及空值的 `--key value` 对
    fn sanitize_game_args(args: Vec<String>) -> Vec<String> {
        let mut out = Vec::new();
        let mut i = 0;
        while i < args.len() {
            let arg = &args[i];
            if !Self::is_valid_launch_arg(arg) {
                if arg.starts_with("--") && i + 1 < args.len() && !args[i + 1].starts_with("--") {
                    i += 2;
                } else {
                    i += 1;
                }
                continue;
            }
            if arg.starts_with("--") {
                if i + 1 < args.len()
                    && !args[i + 1].starts_with("--")
                    && Self::is_valid_launch_arg(&args[i + 1])
                {
                    out.push(arg.clone());
                    out.push(args[i + 1].clone());
                    i += 2;
                } else {
                    i += 1;
                }
                continue;
            }
            out.push(arg.clone());
            i += 1;
        }
        out
    }

    fn build_basic_game_args(config: &LaunchConfig, version_json: &VersionJson) -> Vec<String> {
        vec![
            "--username".into(),
            config.username.clone(),
            "--version".into(),
            config.instance_name.clone(),
            "--gameDir".into(),
            config.game_directory.to_string_lossy().to_string(),
            "--assetsDir".into(),
            config.assets_directory.to_string_lossy().to_string(),
            "--assetIndex".into(),
            Self::asset_index_name(version_json),
            "--uuid".into(),
            config.uuid.clone(),
            "--accessToken".into(),
            config.access_token.clone(),
            "--userType".into(),
            config.user_type.clone(),
            "--versionType".into(),
            config.version_type.clone(),
            "--width".into(),
            config.width.to_string(),
            "--height".into(),
            config.height.to_string(),
        ]
    }

    fn is_library_compatible(lib: &Library) -> bool {
        lib.rules
            .as_ref()
            .map(|r| rules_compatible(r))
            .unwrap_or(true)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_game_args() {
        let config = LaunchConfig {
            username: "TestPlayer".into(),
            uuid: "00000000-0000-0000-0000-000000000000".into(),
            access_token: "test-token".into(),
            instance_name: "1.20.4".into(),
            width: 854,
            height: 480,
            ..Default::default()
        };
        let vj = VersionJson {
            assets: Some("1.21".into()),
            ..Default::default()
        };
        let args = LaunchCommandBuilder::build_basic_game_args(&config, &vj);
        assert!(args.contains(&"TestPlayer".to_string()));
    }
}
