//! # C FFI 接口
//!
//! 为 C++ 前端 (Qt/PyQt) 提供稳定的 FFI 调用接口。
//! 所有函数按照 "spectrum_*" 命名约定导出。
//!
//! 调用约定:
//! - 字符串参数: C 字符串 (const char*, null-terminated)
//! - 字符串返回值: 通过 out_buffer + buffer_size 输出。libc::free 不适用, 应由调用者管理内存
//! - 结构体: 通过不透明指针传递 (void*)
//! - 错误处理: 所有函数返回 i32, 0=成功, -1=错误, 错误信息通过 last_error() 获取
//! - 回调: 进度回调通过函数指针

use crate::*;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::sync::{Mutex, OnceLock};
use tokio::runtime::Runtime;

// ========================================================================
//  全局状态
// ========================================================================

static RUNTIME: OnceLock<Runtime> = OnceLock::new();
static HTTP_CLIENT: OnceLock<HttpClient> = OnceLock::new();
static DOWNLOAD_ENGINE: OnceLock<Mutex<DownloadEngine>> = OnceLock::new();

/// 最后一次错误信息
static LAST_ERROR: Mutex<String> = Mutex::new(String::new());

fn get_runtime() -> &'static Runtime {
    RUNTIME.get_or_init(|| Runtime::new().expect("无法创建 Tokio 运行时"))
}

fn get_http_client() -> &'static HttpClient {
    HTTP_CLIENT.get_or_init(|| HttpClient::new(true))
}

fn get_download_engine() -> &'static Mutex<DownloadEngine> {
    DOWNLOAD_ENGINE.get_or_init(|| Mutex::new(DownloadEngine::new(get_http_client().clone())))
}

// ========================================================================
//  辅助宏
// ========================================================================

/// 辅助: 将 C 字符串转为 Rust &str (如失败则设为默认值)
macro_rules! cstr_to_str {
    ($ptr:expr) => {{
        if $ptr.is_null() {
            ""
        } else {
            match unsafe { CStr::from_ptr($ptr) }.to_str() {
                Ok(s) => s,
                Err(_) => "",
            }
        }
    }};
}

/// 辅助: 将结果写入输出缓冲区
macro_rules! write_output {
    ($dest:expr, $size:expr, $val:expr) => {{
        let c_str = CString::new($val).unwrap_or_default();
        let bytes = c_str.as_bytes_with_nul();
        let len = bytes.len().min($size as usize - 1);
        if !$dest.is_null() && $size > 0 {
            unsafe {
                std::ptr::copy_nonoverlapping(bytes.as_ptr(), $dest as *mut u8, len);
                *$dest.add(len) = 0;
            }
        }
        len as i32
    }};
}

/// 辅助: 捕获错误并设置 LAST_ERROR
macro_rules! catch_ffi {
    ($expr:expr) => {{
        match $expr {
            Ok(val) => val,
            Err(e) => {
                let msg = e.to_string();
                *LAST_ERROR.lock().unwrap() = msg;
                return -1;
            }
        }
    }};
}

// ========================================================================
//  C FFI 导出函数
// ========================================================================

/// 获取最后一次错误信息
#[no_mangle]
pub extern "C" fn spectrum_last_error(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let error = LAST_ERROR.lock().unwrap().clone();
    write_output!(buffer, buffer_size, error)
}

/// 初始化核心库 (在应用启动时调用一次)
#[no_mangle]
pub extern "C" fn spectrum_init(use_bmclapi: bool) -> i32 {
    let rt = Runtime::new().unwrap_or_else(|e| {
        panic!("无法创建 Tokio 运行时: {}", e);
    });
    let client = HttpClient::new(use_bmclapi);

    let _ = RUNTIME.set(rt);
    let _ = HTTP_CLIENT.set(client.clone());
    let _ = DOWNLOAD_ENGINE.set(Mutex::new(DownloadEngine::new(client)));

    log::info!("Spectrum Core 已初始化");
    0
}

// ========================================================================
//  版本清单
// ========================================================================

/// 获取版本列表
#[no_mangle]
pub extern "C" fn spectrum_get_versions(
    include_snapshot: bool,
    include_old_alpha: bool,
    include_old_beta: bool,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let mut engine = get_download_engine().lock().unwrap();
    let versions = catch_ffi!(
        get_runtime().block_on(
            engine.get_version_list(include_snapshot, include_old_alpha, include_old_beta)
        )
    );
    let json = serde_json::to_string(&versions).unwrap_or_else(|_| "[]".into());
    write_output!(buffer, buffer_size, json)
}

/// 获取最新正式版
#[no_mangle]
pub extern "C" fn spectrum_get_latest_release(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let mut engine = get_download_engine().lock().unwrap();
    let version = catch_ffi!(
        get_runtime().block_on(engine.get_latest_release())
    );
    write_output!(buffer, buffer_size, version)
}

/// 获取最新快照版
#[no_mangle]
pub extern "C" fn spectrum_get_latest_snapshot(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let mut engine = get_download_engine().lock().unwrap();
    let version = catch_ffi!(
        get_runtime().block_on(engine.get_latest_snapshot())
    );
    write_output!(buffer, buffer_size, version)
}

// ========================================================================
//  下载 / 安装
// ========================================================================

/// 下载进度回调类型
pub type ProgressCallback = extern "C" fn(stage: *const c_char, current: u64, total: u64);

/// 下载 Minecraft 版本
#[no_mangle]
pub extern "C" fn spectrum_download_version(
    mc_version: *const c_char,
    instance_name: *const c_char,
    minecraft_dir: *const c_char,
    modloader_type: *const c_char,
    progress_cb: Option<ProgressCallback>,
) -> i32 {
    let mc_version = cstr_to_str!(mc_version);
    let instance_name = cstr_to_str!(instance_name);
    let minecraft_dir = cstr_to_str!(minecraft_dir);
    let modloader_type = cstr_to_str!(modloader_type);

    let minecraft_dir = std::path::Path::new(minecraft_dir);
    let modloader = ModLoader::from_str(modloader_type);

    let mut engine = get_download_engine().lock().unwrap();

    // 创建 progress channel
    let (tx, mut rx) = tokio::sync::mpsc::channel::<DownloadEvent>(256);

    // 在后台线程处理进度事件
    std::thread::spawn(move || {
        while let Some(event) = rx.blocking_recv() {
            match event {
                DownloadEvent::Progress { stage, current, total } => {
                    if let Some(cb) = progress_cb {
                        let stage_str = CString::new(stage.to_string()).unwrap_or_default();
                        cb(stage_str.as_ptr(), current, total);
                    }
                }
                DownloadEvent::FileCompleted { name, success } => {
                    log::debug!("文件下载完成: {} (success={})", name, success);
                }
                DownloadEvent::Completed => {
                    log::info!("下载完成");
                    break;
                }
                DownloadEvent::Error(msg) => {
                    log::error!("下载错误: {}", msg);
                    *LAST_ERROR.lock().unwrap() = msg;
                    break;
                }
            }
        }
    });

    catch_ffi!(
        get_runtime().block_on(
            engine.download_version(mc_version, instance_name, minecraft_dir, modloader, tx)
        )
    );

    0
}

// ========================================================================
//  启动
// ========================================================================

/// 启动 Minecraft
///
/// 返回构建好的命令行参数列表 (JSON 字符串数组)
#[no_mangle]
pub extern "C" fn spectrum_get_launch_command(
    instance_name: *const c_char,
    minecraft_dir: *const c_char,
    java_path: *const c_char,
    username: *const c_char,
    uuid: *const c_char,
    access_token: *const c_char,
    xmx: *const c_char,
    xms: *const c_char,
    width: i32,
    height: i32,
    server_ip: *const c_char,
    server_port: i32,
    extra_jvm_args: *const c_char,
    extra_game_args: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let instance_name = cstr_to_str!(instance_name);
    let minecraft_dir = cstr_to_str!(minecraft_dir);
    let java_path = cstr_to_str!(java_path);
    let username = cstr_to_str!(username);
    let uuid = cstr_to_str!(uuid);
    let access_token = cstr_to_str!(access_token);
    let xmx = cstr_to_str!(xmx);
    let xms = cstr_to_str!(xms);
    let server_ip = cstr_to_str!(server_ip);
    let extra_jvm_args = cstr_to_str!(extra_jvm_args);
    let extra_game_args = cstr_to_str!(extra_game_args);

    let minecraft_dir = std::path::Path::new(minecraft_dir);
    let instance_dir = minecraft_dir.join("versions").join(instance_name);
    let json_path = instance_dir.join(format!("{}.json", instance_name));

    // 加载并合并 version.json（含 inheritsFrom）
    let client = get_http_client().clone();
    let vj = catch_ffi!(get_runtime().block_on(async {
        let mut mgr = VersionJsonManager::new(client.clone());
        let mut manifest_mgr = ManifestManager::new(client);
        mgr.resolve_instance_json(&json_path, &mut manifest_mgr).await
    }));

    let natives_dir = crate::natives::natives_dir(&instance_dir, instance_name);

    // 构建配置
    let config = LaunchConfig {
        java_path: java_path.to_string(),
        xmx: xmx.to_string(),
        xms: xms.to_string(),
        minecraft_dir: minecraft_dir.to_path_buf(),
        instance_name: instance_name.to_string(),
        username: username.to_string(),
        uuid: uuid.to_string(),
        access_token: access_token.to_string(),
        game_directory: instance_dir.clone(),
        assets_directory: minecraft_dir.join("assets"),
        libraries_directory: minecraft_dir.join("libraries"),
        natives_directory: natives_dir,
        width: width as u32,
        height: height as u32,
        extra_jvm_args: extra_jvm_args.to_string(),
        extra_game_args: extra_game_args.to_string(),
        server_ip: if server_ip.is_empty() { None } else { Some(server_ip.to_string()) },
        server_port: if server_port > 0 { Some(server_port as u16) } else { None },
        ..Default::default()
    };

    let args = catch_ffi!(LaunchCommandBuilder::build_command(&config, &vj));
    let json = serde_json::to_string(&args).unwrap_or_else(|_| "[]".into());
    write_output!(buffer, buffer_size, json)
}

// ========================================================================
//  Java 检测
// ========================================================================

/// 查找系统 Java
///
/// 返回 JSON 数组: [{"path": "...", "major_version": 17, ...}]
#[no_mangle]
pub extern "C" fn spectrum_find_java(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let javas = JavaDetector::find_all();
    let json = serde_json::to_string(&javas).unwrap_or_else(|_| "[]".into());
    write_output!(buffer, buffer_size, json)
}

/// 获取单个 Java 信息
#[no_mangle]
pub extern "C" fn spectrum_get_java_info(
    java_path: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let path = cstr_to_str!(java_path);
    let info = JavaDetector::get_java_info(std::path::Path::new(path));
    let json = serde_json::to_string(&info).unwrap_or_else(|_| "null".into());
    write_output!(buffer, buffer_size, json)
}

// ========================================================================
//  实例管理
// ========================================================================

/// 列出所有已安装的实例
#[no_mangle]
pub extern "C" fn spectrum_list_instances(
    minecraft_dir: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let dir = cstr_to_str!(minecraft_dir);
    let manager = InstanceManager::new(std::path::PathBuf::from(dir));
    let instances = catch_ffi!(manager.list_instances());
    let json = serde_json::to_string(&instances).unwrap_or_else(|_| "[]".into());
    write_output!(buffer, buffer_size, json)
}

/// 删除实例
#[no_mangle]
pub extern "C" fn spectrum_delete_instance(
    minecraft_dir: *const c_char,
    instance_name: *const c_char,
) -> i32 {
    let dir = cstr_to_str!(minecraft_dir);
    let name = cstr_to_str!(instance_name);
    let manager = InstanceManager::new(std::path::PathBuf::from(dir));
    catch_ffi!(manager.delete_instance(name));
    0
}

/// 重命名实例
#[no_mangle]
pub extern "C" fn spectrum_rename_instance(
    minecraft_dir: *const c_char,
    old_name: *const c_char,
    new_name: *const c_char,
) -> i32 {
    let dir = cstr_to_str!(minecraft_dir);
    let old = cstr_to_str!(old_name);
    let new = cstr_to_str!(new_name);
    let manager = InstanceManager::new(std::path::PathBuf::from(dir));
    catch_ffi!(manager.rename_instance(old, new));
    0
}

// ========================================================================
//  ModLoader 支持
// ========================================================================

/// 获取 ModLoader 支持的版本列表
#[no_mangle]
pub extern "C" fn spectrum_get_modloader_versions(
    modloader_type: *const c_char,
    mc_version: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let mt = cstr_to_str!(modloader_type);
    let mc = cstr_to_str!(mc_version);

    let loader = ModLoader::from_str(mt);
    let installer = match modloader::get_installer(get_http_client().clone(), loader) {
        Some(i) => i,
        None => {
            let json = "[]";
            return write_output!(buffer, buffer_size, json);
        }
    };

    let versions = catch_ffi!(
        get_runtime().block_on(installer.get_loader_versions(mc))
    );
    let json = serde_json::to_string(&versions).unwrap_or_else(|_| "[]".into());
    write_output!(buffer, buffer_size, json)
}

/// 安装 ModLoader
#[no_mangle]
pub extern "C" fn spectrum_install_modloader(
    modloader_type: *const c_char,
    mc_version: *const c_char,
    loader_version: *const c_char,
    instance_dir: *const c_char,
    minecraft_dir: *const c_char,
) -> i32 {
    let mt = cstr_to_str!(modloader_type);
    let mc = cstr_to_str!(mc_version);
    let lv = cstr_to_str!(loader_version);
    let inst_dir = cstr_to_str!(instance_dir);
    let mc_dir = cstr_to_str!(minecraft_dir);

    let loader = ModLoader::from_str(mt);
    let installer = match modloader::get_installer(get_http_client().clone(), loader) {
        Some(i) => i,
        None => return -1,
    };

    let lv_opt = if lv.is_empty() { None } else { Some(lv) };

    catch_ffi!(
        get_runtime().block_on(
            installer.install(mc, lv_opt, std::path::Path::new(inst_dir), std::path::Path::new(mc_dir))
        )
    );
    0
}

// ========================================================================
//  OAuth 认证
// ========================================================================

/// 执行 Microsoft OAuth 认证
///
/// 返回 JSON: {"access_token": "...", "refresh_token": "...", "uuid": "...", "username": "..."}
#[no_mangle]
pub extern "C" fn spectrum_oauth_authenticate(
    client_id: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let client_id = cstr_to_str!(client_id);
    let client_id_opt = if client_id.is_empty() { None } else { Some(client_id.to_string()) };

    let oauth = OAuthClient::new(get_http_client().clone(), client_id_opt);
    let result = catch_ffi!(get_runtime().block_on(oauth.authenticate()));
    let json = serde_json::to_string(&result).unwrap_or_else(|_| "{}".into());
    write_output!(buffer, buffer_size, json)
}

/// 刷新 OAuth Token
#[no_mangle]
pub extern "C" fn spectrum_oauth_refresh(
    client_id: *const c_char,
    refresh_token: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let client_id = cstr_to_str!(client_id);
    let refresh_token = cstr_to_str!(refresh_token);
    let client_id_opt = if client_id.is_empty() { None } else { Some(client_id.to_string()) };

    let oauth = OAuthClient::new(get_http_client().clone(), client_id_opt);
    let result = catch_ffi!(get_runtime().block_on(oauth.refresh_access_token(refresh_token)));
    let json = serde_json::to_string(&result).unwrap_or_else(|_| "{}".into());
    write_output!(buffer, buffer_size, json)
}

// ========================================================================
//  配置管理
// ========================================================================

/// 加载配置
#[no_mangle]
pub extern "C" fn spectrum_load_config(
    path: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let path = cstr_to_str!(path);
    let config = catch_ffi!(LauncherConfig::load(std::path::Path::new(path)));
    let json = serde_json::to_string(&config).unwrap_or_else(|_| "{}".into());
    write_output!(buffer, buffer_size, json)
}

/// 保存配置
#[no_mangle]
pub extern "C" fn spectrum_save_config(
    path: *const c_char,
    config_json: *const c_char,
) -> i32 {
    let path = cstr_to_str!(path);
    let json = cstr_to_str!(config_json);
    let config: LauncherConfig = catch_ffi!(serde_json::from_str(json));
    catch_ffi!(config.save(std::path::Path::new(path)));
    0
}

// ========================================================================
//  Utils
// ========================================================================

/// Maven 坐标转路径
#[no_mangle]
pub extern "C" fn spectrum_maven_to_path(
    maven_str: *const c_char,
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let maven = cstr_to_str!(maven_str);
    let path = match maven_to_path(maven) {
        Ok(p) => p,
        Err(e) => {
            *LAST_ERROR.lock().unwrap() = e.to_string();
            return -1;
        }
    };
    write_output!(buffer, buffer_size, path)
}

/// 获取当前操作系统
#[no_mangle]
pub extern "C" fn spectrum_native_os(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let os = native_os();
    write_output!(buffer, buffer_size, os)
}

/// 获取当前架构
#[no_mangle]
pub extern "C" fn spectrum_get_architecture(
    buffer: *mut c_char,
    buffer_size: i32,
) -> i32 {
    let arch = get_architecture();
    write_output!(buffer, buffer_size, arch)
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_maven_to_path_ffi() {
        let mut buf = [0u8; 256];
        let result = spectrum_maven_to_path(
            "net.minecraft:launchwrapper:1.12\0".as_ptr() as *const c_char,
            buf.as_mut_ptr() as *mut c_char,
            256,
        );
        assert!(result > 0);
        let output = unsafe { CStr::from_ptr(buf.as_ptr() as *const c_char) };
        assert_eq!(output.to_str().unwrap(), "net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar");
    }

    #[test]
    fn test_os_ffi() {
        let mut buf = [0u8; 32];
        let result = spectrum_native_os(buf.as_mut_ptr() as *mut c_char, 32);
        assert!(result > 0);
    }
}
