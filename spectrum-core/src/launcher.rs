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

        // version JSON 中的 JVM 参数模板
        Self::append_jvm_arguments(&mut args, version_json, config);

        if !config.extra_jvm_args.is_empty() {
            for extra in config.extra_jvm_args.split_whitespace() {
                args.push(extra.to_string());
            }
        }

        let classpath = Self::build_classpath(config, version_json)?;
        args.push("-cp".into());
        args.push(classpath);
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

    /// 追加 version JSON 中的 JVM 参数（跳过 -cp / ${classpath}）
    fn append_jvm_arguments(args: &mut Vec<String>, vj: &VersionJson, config: &LaunchConfig) {
        let Some(ref arguments) = vj.arguments else {
            return;
        };
        if arguments.jvm.is_empty() {
            return;
        }

        let skip = ["-cp", "-classpath", "${classpath}"];
        for arg in &arguments.jvm {
            match arg {
                Argument::Value(s) if skip.iter().any(|x| s.contains(x)) => continue,
                Argument::Value(s) => {
                    let v = Self::replace_tokens(s, config, vj);
                    if Self::is_valid_launch_arg(&v) {
                        args.push(v);
                    }
                }
                Argument::Rules { rules, value } if rules_compatible(rules) => {
                    let values = match value {
                        ArgumentValue::Single(s) => vec![Self::replace_tokens(s, config, vj)],
                        ArgumentValue::Multi(v) => v
                            .iter()
                            .map(|s| Self::replace_tokens(s, config, vj))
                            .collect(),
                    };
                    for v in values {
                        if skip.iter().any(|x| v.contains(x)) {
                            continue;
                        }
                        if Self::is_valid_launch_arg(&v) {
                            args.push(v);
                        }
                    }
                }
                Argument::Rules { .. } => {}
            }
        }
    }

    fn build_classpath(config: &LaunchConfig, version_json: &VersionJson) -> CoreResult<String> {
        let mut paths = Vec::new();

        // client jar — 优先 instance_name.jar
        let jar_candidates = [
            config.game_directory.join(format!("{}.jar", config.instance_name)),
            config
                .game_directory
                .join(format!("{}.jar", version_json.id)),
        ];
        for jar in jar_candidates {
            if jar.exists() {
                paths.push(jar);
                break;
            }
        }

        for lib in &version_json.libraries {
            if !Self::is_library_compatible(lib) {
                continue;
            }

            if let Some(ref dl) = lib.downloads {
                if let Some(ref artifact) = dl.artifact {
                    let lib_path = config.libraries_directory.join(&artifact.path);
                    if lib_path.exists() {
                        paths.push(lib_path);
                        continue;
                    }
                }
            }

            if let Ok(maven_path) = maven_to_path(&lib.name) {
                let lib_path = config.libraries_directory.join(&maven_path);
                if lib_path.exists() {
                    paths.push(lib_path);
                }
            }
        }

        let sep = if cfg!(target_os = "windows") { ";" } else { ":" };
        Ok(paths
            .iter()
            .map(|p| p.to_string_lossy().to_string())
            .collect::<Vec<_>>()
            .join(sep))
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

    fn replace_tokens(template: &str, config: &LaunchConfig, version_json: &VersionJson) -> String {
        template
            .replace("${auth_player_name}", &config.username)
            .replace("${version_name}", &config.instance_name)
            .replace("${game_directory}", &config.game_directory.to_string_lossy())
            .replace("${game_assets}", &config.assets_directory.to_string_lossy())
            .replace("${assets_root}", &config.assets_directory.to_string_lossy())
            .replace(
                "${assets_index_name}",
                version_json.assets.as_deref().unwrap_or("legacy"),
            )
            .replace("${auth_uuid}", &config.uuid)
            .replace("${auth_access_token}", &config.access_token)
            .replace("${user_type}", &config.user_type)
            .replace("${version_type}", &config.version_type)
            .replace("${resolution_width}", &config.width.to_string())
            .replace("${resolution_height}", &config.height.to_string())
            .replace("${natives_directory}", &config.natives_directory.to_string_lossy())
            .replace("${launcher_name}", "Spectrum Launcher")
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
            version_json
                .assets
                .clone()
                .unwrap_or_else(|| "legacy".into()),
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
