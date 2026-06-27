//! # PyO3 Python 绑定
//!
//! 供 `main.py` 通过 `import _spectrum_core` 调用 Rust 异步核心。

use crate::download::{AutoDownloadOptions, DownloadEngine};
use crate::http_client::HttpClient;
use crate::launcher::LaunchCommandBuilder;
use crate::manager::InstanceManager;
use crate::manifest::VersionJsonManager;
use crate::oauth::OAuthClient;
use crate::java::JavaDetector;
use crate::types::*;

use pyo3::exceptions::{PyOSError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::path::{Path, PathBuf};
use std::sync::OnceLock;
use tokio::runtime::Runtime;
use tokio::sync::mpsc;

static HTTP_CLIENT: OnceLock<HttpClient> = OnceLock::new();
static LOGGER_INIT: OnceLock<()> = OnceLock::new();

/// 在独立线程上创建 Tokio Runtime 执行异步任务，避免多线程 `block_on` 同一 Runtime 死锁。
///
/// 必须在 `py.allow_threads` 内阻塞等待：否则 `auto_download` 的进度线程无法
/// 通过 `Python::with_gil` 回调 Python（调用方线程持锁 join → 永久卡死）。
fn run_async<F, T>(py: Python<'_>, future: F) -> PyResult<T>
where
    F: std::future::Future<Output = CoreResult<T>> + Send + 'static,
    T: Send + 'static,
{
    py.allow_threads(|| {
        std::thread::spawn(move || {
            Runtime::new()
                .expect("tokio runtime")
                .block_on(future)
        })
        .join()
        .map_err(|_| PyRuntimeError::new_err("async worker panicked"))?
        .map_err(py_err)
    })
}

fn ensure_logger() {
    LOGGER_INIT.get_or_init(|| {
        let _ = env_logger::Builder::from_default_env()
            .filter_level(log::LevelFilter::Info)
            .format(|buf, record| {
                use std::io::Write;
                writeln!(
                    buf,
                    "[RUST][{}] {}",
                    record.level(),
                    record.args()
                )
            })
            .try_init();
    });
}

fn progress_description(stage: &DownloadStage, current: u64, total: u64) -> String {
    // 与 main.py progress_callback 解析格式一致: [LIB][cur/tot] / [AST][cur/tot]
    let tag = match stage {
        DownloadStage::Libraries => "LIB",
        DownloadStage::Assets => "AST",
        DownloadStage::ClientJar => "JAR",
        DownloadStage::VersionJson => "JSON",
        DownloadStage::FetchingManifest => "MAN",
        DownloadStage::ModLoader => "MOD",
    };
    format!("[{tag}][{current}/{total}]")
}

fn http() -> &'static HttpClient {
    HTTP_CLIENT.get_or_init(|| HttpClient::new(true))
}

fn py_err<T: std::fmt::Display>(e: T) -> PyErr {
    PyRuntimeError::new_err(e.to_string())
}

/// 初始化 Rust 核心（BMCLAPI 开关）
#[pyfunction]
#[pyo3(signature = (use_bmclapi=true))]
fn init(use_bmclapi: bool) -> PyResult<()> {
    ensure_logger();
    HTTP_CLIENT.get_or_init(|| HttpClient::new(use_bmclapi));
    Ok(())
}

#[pyfunction]
#[pyo3(signature = (show_snapshot=false, show_old_alpha=false, show_old_beta=false, bmclapi=true))]
fn get_version_list(
    py: Python<'_>,
    show_snapshot: bool,
    show_old_alpha: bool,
    show_old_beta: bool,
    bmclapi: bool,
) -> PyResult<Vec<String>> {
    init(bmclapi)?;
    let client = http().clone();
    run_async(py, async move {
        let mut eng = DownloadEngine::new(client);
        eng.get_version_list(show_snapshot, show_old_alpha, show_old_beta).await
    })
}

#[pyfunction]
#[pyo3(signature = (mcversion, bmclapi=true))]
fn get_version_json(py: Python<'_>, mcversion: &str, bmclapi: bool) -> PyResult<PyObject> {
    init(bmclapi)?;
    let client = http().clone();
    let mcversion = mcversion.to_string();
    let vj = run_async(py, async move {
        let mut mgr = VersionJsonManager::new(client.clone());
        let mut manifest = crate::manifest::ManifestManager::new(client);
        mgr.get_version_json(&mcversion, &mut manifest).await
    })?;
    let json_str = serde_json::to_string(&vj).map_err(py_err)?;
    Ok(py
        .import("json")?
        .call_method1("loads", (json_str,))?
        .into())
}

#[pyfunction]
#[pyo3(signature = (
    minecraft_dir,
    mcversion,
    instance_name,
    modloader="vanilla",
    modloader_version=None,
    bmclapi=true,
    progress_callback=None
))]
fn auto_download(
    py: Python<'_>,
    minecraft_dir: &str,
    mcversion: &str,
    instance_name: &str,
    modloader: &str,
    modloader_version: Option<&str>,
    bmclapi: bool,
    progress_callback: Option<PyObject>,
) -> PyResult<()> {
    init(bmclapi)?;

    let ml_ver = modloader_version
        .filter(|v| !v.is_empty() && *v != "latest")
        .map(String::from);

    let (tx, mut rx) = mpsc::channel::<DownloadEvent>(256);
    let progress_cb = progress_callback.as_ref().map(|cb| cb.clone_ref(py));

    let progress_handle = std::thread::spawn(move || {
        while let Some(event) = rx.blocking_recv() {
            match event {
                DownloadEvent::Progress { stage, current, total } => {
                    if let Some(ref cb) = progress_cb {
                        Python::with_gil(|py| {
                            let desc = progress_description(&stage, current, total);
                            let _ = cb.call1(py, (current, total, desc));
                        });
                    }
                }
                DownloadEvent::Completed => break,
                DownloadEvent::Error(msg) => {
                    log::error!("download error: {msg}");
                    break;
                }
                _ => {}
            }
        }
    });

    let minecraft_dir = minecraft_dir.to_string();
    let mcversion = mcversion.to_string();
    let instance_name = instance_name.to_string();
    let modloader = modloader.to_string();

    let client = http().clone();
    let result = run_async(py, async move {
        let mut eng = DownloadEngine::new(client);
        eng.auto_download(
            Path::new(&minecraft_dir),
            AutoDownloadOptions {
                mc_version: mcversion,
                instance_name,
                modloader: ModLoader::from_str(&modloader),
                modloader_version: ml_ver,
            },
            tx,
        )
        .await
        .map(|_| ())
    });
    let _ = progress_handle.join();
    result
}

#[pyfunction]
fn get_minecraft_version(minecraft_dir: &str, instance_name: &str) -> PyResult<String> {
    let json_path = PathBuf::from(minecraft_dir)
        .join("versions")
        .join(instance_name)
        .join(format!("{instance_name}.json"));
    let content = std::fs::read_to_string(&json_path)
        .map_err(|e| PyOSError::new_err(format!("read version json: {e}")))?;
    let vj: VersionJson = serde_json::from_str(&content).map_err(py_err)?;
    Ok(VersionJsonManager::get_minecraft_version(&vj))
}

#[pyfunction]
fn get_required_java_version(py: Python<'_>, minecraft_dir: &str, instance_name: &str) -> PyResult<i32> {
    let json_path = PathBuf::from(minecraft_dir)
        .join("versions")
        .join(instance_name)
        .join(format!("{instance_name}.json"));
    let client = http().clone();
    let vj = run_async(py, async move {
        let mut mgr = VersionJsonManager::new(client.clone());
        let mut manifest = crate::manifest::ManifestManager::new(client);
        mgr.resolve_instance_json(&json_path, &mut manifest).await
    })?;
    Ok(VersionJsonManager::get_required_java_version(&vj))
}

#[pyfunction]
#[pyo3(signature = (
    javaw,
    xmx,
    minecraft_dir,
    instance_name,
    username="Steve",
    xmn="256M",
    ms_login=false,
    access_token=None,
    width=854,
    height=480,
    version_type="release",
    jvm_args="",
    game_args_extend="",
    uuid=None
))]
#[allow(clippy::too_many_arguments)]
fn build_launch_script(
    py: Python<'_>,
    javaw: &str,
    xmx: &str,
    minecraft_dir: &str,
    instance_name: &str,
    username: &str,
    xmn: &str,
    ms_login: bool,
    access_token: Option<&str>,
    width: i32,
    height: i32,
    version_type: &str,
    jvm_args: &str,
    game_args_extend: &str,
    uuid: Option<&str>,
) -> PyResult<String> {
    let minecraft_dir = minecraft_dir.replace('\\', "/");
    let instance_dir = PathBuf::from(&minecraft_dir)
        .join("versions")
        .join(instance_name);
    let json_path = instance_dir.join(format!("{instance_name}.json"));

    let client = http().clone();
    let vj = run_async(py, async move {
        let mut mgr = VersionJsonManager::new(client.clone());
        let mut manifest = crate::manifest::ManifestManager::new(client);
        mgr.resolve_instance_json(&json_path, &mut manifest).await
    })?;

    let player_uuid = uuid
        .map(String::from)
        .unwrap_or_else(|| "00000000000000000000000000000000".into());
    let token = match (ms_login, access_token) {
        (true, Some(t)) => t.to_string(),
        (true, None) => return Err(PyValueError::new_err("ms_login 需要 access_token")),
        (false, Some(t)) => t.to_string(),
        (false, None) => player_uuid.clone(),
    };
    let user_type = if ms_login { "msa" } else { "legacy" };

    let natives = crate::natives::natives_dir(&instance_dir, instance_name);
    let mut extra_jvm = jvm_args.to_string();
    if !xmn.is_empty() {
        extra_jvm = format!("-Xmn{xmn} {extra_jvm}");
    }

    let config = LaunchConfig {
        java_path: javaw.to_string(),
        xmx: xmx.to_string(),
        xms: String::new(),
        minecraft_dir: PathBuf::from(&minecraft_dir),
        instance_name: instance_name.to_string(),
        username: username.to_string(),
        uuid: player_uuid,
        access_token: token,
        user_type: user_type.into(),
        version_type: version_type.to_string(),
        game_directory: instance_dir.clone(),
        assets_directory: PathBuf::from(&minecraft_dir).join("assets"),
        libraries_directory: PathBuf::from(&minecraft_dir).join("libraries"),
        natives_directory: natives,
        width: width as u32,
        height: height as u32,
        extra_jvm_args: extra_jvm.trim().to_string(),
        extra_game_args: game_args_extend.to_string(),
        ..Default::default()
    };

    let args = LaunchCommandBuilder::build_command(&config, &vj).map_err(py_err)?;
    let cmd_part = shell_join(&args);

    Ok(format!(
        "cd {minecraft_dir}/versions/{instance_name} && {cmd_part}"
    ))
}

fn shell_join(args: &[String]) -> String {
    args.iter()
        .map(|a| {
            if a.contains(' ') || a.contains('"') {
                format!("\"{}\"", a.replace('"', "\\\""))
            } else {
                a.clone()
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

#[pyfunction]
fn find_javas(py: Python<'_>) -> PyResult<PyObject> {
    let list = PyList::empty(py);
    for j in JavaDetector::find_all() {
        let dict = PyDict::new(py);
        dict.set_item("path", j.path.to_string_lossy().as_ref())?;
        dict.set_item("major_version", j.major_version)?;
        dict.set_item("full_version", j.full_version)?;
        dict.set_item("is_jre", j.is_jre)?;
        list.append(dict)?;
    }
    Ok(list.into())
}

#[pyfunction]
fn get_java_version(java_path: &str) -> PyResult<i32> {
    JavaDetector::get_java_info(Path::new(java_path))
        .map(|j| j.major_version)
        .ok_or_else(|| PyValueError::new_err(format!("无法解析 Java: {java_path}")))
}

#[pyfunction]
fn oauth_authenticate(py: Python<'_>) -> PyResult<PyObject> {
    let client = OAuthClient::new(http().clone(), None);
    let result = run_async(py, async move { client.authenticate().await })?;
    let dict = PyDict::new(py);
    dict.set_item("access_token", result.access_token)?;
    dict.set_item("refresh_token", result.refresh_token)?;
    dict.set_item("uuid", result.uuid)?;
    dict.set_item("username", result.username)?;
    Ok(dict.into())
}

#[pyfunction]
fn oauth_refresh(py: Python<'_>, refresh_token: &str) -> PyResult<PyObject> {
    let client = OAuthClient::new(http().clone(), None);
    let refresh_token = refresh_token.to_string();
    let result = run_async(py, async move { client.refresh_access_token(&refresh_token).await })?;
    let dict = PyDict::new(py);
    dict.set_item("access_token", result.access_token)?;
    dict.set_item("refresh_token", result.refresh_token)?;
    dict.set_item("uuid", result.uuid)?;
    dict.set_item("username", result.username)?;
    Ok(dict.into())
}

#[pyfunction]
fn get_mslogin_uuid_name(py: Python<'_>, access_token: &str) -> PyResult<(String, String)> {
    let client = OAuthClient::new(http().clone(), None);
    let access_token = access_token.to_string();
    run_async(py, async move { client.get_profile_from_token(&access_token).await })
}

#[pyfunction]
fn list_instances(minecraft_dir: &str) -> PyResult<Vec<String>> {
    let mgr = InstanceManager::new(PathBuf::from(minecraft_dir));
    mgr.list_instances().map_err(py_err)
}

#[pyfunction]
fn remove_version(minecraft_dir: &str, instance_name: &str) -> PyResult<()> {
    let mgr = InstanceManager::new(PathBuf::from(minecraft_dir));
    mgr.delete_instance(instance_name).map_err(py_err)
}

#[pyfunction]
fn rename_version(minecraft_dir: &str, old_name: &str, new_name: &str) -> PyResult<()> {
    let mgr = InstanceManager::new(PathBuf::from(minecraft_dir));
    mgr.rename_instance(old_name, new_name).map_err(py_err)
}

#[pyfunction]
fn get_saves(minecraft_dir: &str, instance: &str) -> PyResult<Vec<String>> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .get_saves(instance)
        .map_err(py_err)
}

#[pyfunction]
fn get_mods(minecraft_dir: &str, instance: &str) -> PyResult<Vec<String>> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .get_mods(instance)
        .map_err(py_err)
}

#[pyfunction]
fn get_resourcepacks(minecraft_dir: &str, instance: &str) -> PyResult<Vec<String>> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .get_resourcepacks(instance)
        .map_err(py_err)
}

#[pyfunction]
fn get_shaderpacks(minecraft_dir: &str, instance: &str) -> PyResult<Vec<String>> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .get_shaderpacks(instance)
        .map_err(py_err)
}

#[pyfunction]
fn remove_save(minecraft_dir: &str, instance: &str, name: &str) -> PyResult<()> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .remove_save(instance, name)
        .map_err(py_err)
}

#[pyfunction]
fn remove_mod(minecraft_dir: &str, instance: &str, name: &str) -> PyResult<()> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .remove_mod(instance, name)
        .map_err(py_err)
}

#[pyfunction]
fn remove_resourcepack(minecraft_dir: &str, instance: &str, name: &str) -> PyResult<()> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .remove_resourcepack(instance, name)
        .map_err(py_err)
}

#[pyfunction]
fn remove_shaderpack(minecraft_dir: &str, instance: &str, name: &str) -> PyResult<()> {
    InstanceManager::new(PathBuf::from(minecraft_dir))
        .remove_shaderpack(instance, name)
        .map_err(py_err)
}

#[pyfunction]
fn native_os_py() -> &'static str {
    native_os()
}

#[pyfunction]
fn maven_to_path_py(maven: &str) -> PyResult<String> {
    maven_to_path(maven).map_err(py_err)
}

#[pyfunction]
fn is_rust_core() -> bool {
    true
}

/// 注册 PyO3 模块
pub fn init_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(init, m)?)?;
    m.add_function(wrap_pyfunction!(get_version_list, m)?)?;
    m.add_function(wrap_pyfunction!(get_version_json, m)?)?;
    m.add_function(wrap_pyfunction!(auto_download, m)?)?;
    m.add_function(wrap_pyfunction!(get_minecraft_version, m)?)?;
    m.add_function(wrap_pyfunction!(get_required_java_version, m)?)?;
    m.add_function(wrap_pyfunction!(build_launch_script, m)?)?;
    m.add_function(wrap_pyfunction!(find_javas, m)?)?;
    m.add_function(wrap_pyfunction!(get_java_version, m)?)?;
    m.add_function(wrap_pyfunction!(oauth_authenticate, m)?)?;
    m.add_function(wrap_pyfunction!(oauth_refresh, m)?)?;
    m.add_function(wrap_pyfunction!(get_mslogin_uuid_name, m)?)?;
    m.add_function(wrap_pyfunction!(list_instances, m)?)?;
    m.add_function(wrap_pyfunction!(remove_version, m)?)?;
    m.add_function(wrap_pyfunction!(rename_version, m)?)?;
    m.add_function(wrap_pyfunction!(get_saves, m)?)?;
    m.add_function(wrap_pyfunction!(get_mods, m)?)?;
    m.add_function(wrap_pyfunction!(get_resourcepacks, m)?)?;
    m.add_function(wrap_pyfunction!(get_shaderpacks, m)?)?;
    m.add_function(wrap_pyfunction!(remove_save, m)?)?;
    m.add_function(wrap_pyfunction!(remove_mod, m)?)?;
    m.add_function(wrap_pyfunction!(remove_resourcepack, m)?)?;
    m.add_function(wrap_pyfunction!(remove_shaderpack, m)?)?;
    m.add_function(wrap_pyfunction!(native_os_py, m)?)?;
    m.add_function(wrap_pyfunction!(maven_to_path_py, m)?)?;
    m.add_function(wrap_pyfunction!(is_rust_core, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
