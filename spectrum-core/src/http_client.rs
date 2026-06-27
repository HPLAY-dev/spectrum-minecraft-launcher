//! # HTTP 客户端统一封装
//!
//! 提供统一的 HTTP 请求接口，支持：
//! - BMCLAPI 镜像切换
//! - 自动重试
//! - 并发限制
//! - 进度回调

use crate::types::*;
use reqwest::Client;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Semaphore;
use tokio::time::sleep;

/// 统一 HTTP 客户端
#[derive(Debug, Clone)]
pub struct HttpClient {
    /// 内部的 reqwest Client
    client: Client,
    /// 并发请求信号量 (限制最大并行数)
    concurrency: Arc<Semaphore>,
    /// 是否使用 BMCLAPI 镜像
    bmclapi: bool,
    /// 最大重试次数
    max_retries: u32,
}

impl Default for HttpClient {
    fn default() -> Self {
        Self::new(false)
    }
}

impl HttpClient {
    /// 创建新的 HTTP 客户端
    pub fn new(bmclapi: bool) -> Self {
        let user_agent = format!(
            "SpectrumLauncher/{} ({})",
            env!("CARGO_PKG_VERSION", "0.1.0"),
            std::env::consts::OS
        );

        let client = Client::builder()
            .user_agent(&user_agent)
            .timeout(Duration::from_secs(120))
            .connect_timeout(Duration::from_secs(30))
            .pool_max_idle_per_host(4)
            .tcp_keepalive(Some(Duration::from_secs(60)))
            .build()
            .expect("创建 HTTP 客户端失败");

        Self {
            client,
            concurrency: Arc::new(Semaphore::new(16)),
            bmclapi,
            max_retries: 3,
        }
    }

    /// 设置并发限制
    pub fn with_concurrency(mut self, max: usize) -> Self {
        self.concurrency = Arc::new(Semaphore::new(max));
        self
    }

    /// 设置最大重试次数
    pub fn with_retries(mut self, retries: u32) -> Self {
        self.max_retries = retries;
        self
    }

    /// 获取是否使用 BMCLAPI
    pub fn use_bmclapi(&self) -> bool {
        self.bmclapi
    }

    /// 切换 BMCLAPI 模式
    pub fn set_bmclapi(&mut self, enabled: bool) {
        self.bmclapi = enabled;
    }

    // ====================================================================
    //  核心 HTTP 方法
    // ====================================================================

    /// 发起 GET 请求并返回文本 (自动重试)
    pub async fn get_text(&self, url: &str) -> CoreResult<String> {
        self.get_with_retry(url, |resp| resp.text()).await
    }

    /// 发起 GET 请求并返回 JSON (自动重试 + 反序列化)
    pub async fn get_json<T: serde::de::DeserializeOwned + Send>(&self, url: &str) -> CoreResult<T> {
        self.get_with_retry(url, |resp| resp.json::<T>()).await
    }

    /// 发起 GET 请求并返回字节数组 (自动重试)
    pub async fn get_bytes(&self, url: &str) -> CoreResult<Vec<u8>> {
        self.get_with_retry(url, |resp| resp.bytes()).await.map(|b| b.to_vec())
    }

    /// 带重试和并发控制的 GET 请求
    async fn get_with_retry<F, Fut, T>(&self, url: &str, extractor: F) -> CoreResult<T>
    where
        F: Fn(reqwest::Response) -> Fut + Send + Sync,
        Fut: std::future::Future<Output = Result<T, reqwest::Error>> + Send,
        T: Send,
    {
        // 获取并发许可
        let _permit = self
            .concurrency
            .acquire()
            .await
            .map_err(|e| CoreError::Unknown(format!("信号量错误: {}", e)))?;

        let mut last_error = None;

        for attempt in 0..=self.max_retries {
            if attempt > 0 {
                // 指数退避
                let delay = Duration::from_millis(500 * 2u64.pow(attempt - 1));
                sleep(delay).await;
                log::warn!("重试请求 [{}/{}]: {}", attempt, self.max_retries, url);
            }

            match self.client.get(url).send().await {
                Ok(response) => {
                    let status = response.status();
                    if status.is_success() {
                        match extractor(response).await {
                            Ok(data) => return Ok(data),
                            Err(e) => {
                                last_error = Some(CoreError::Http(e));
                                continue;
                            }
                        }
                    } else if status.as_u16() == 404 {
                        return Err(CoreError::VersionNotFound(format!(
                            "资源不存在 (404): {}",
                            url
                        )));
                    } else if status.is_server_error() {
                        last_error = Some(CoreError::Network(format!(
                            "服务器错误 ({}): {}",
                            status.as_u16(),
                            url
                        )));
                        continue; // 服务端错误, 重试
                    } else {
                        return Err(CoreError::Network(format!(
                            "HTTP {}: {}",
                            status.as_u16(),
                            url
                        )));
                    }
                }
                Err(e) => {
                    if e.is_timeout() || e.is_connect() {
                        last_error = Some(CoreError::Network(format!(
                            "连接失败: {}",
                            e
                        )));
                        continue; // 网络问题, 重试
                    }
                    return Err(CoreError::Http(e));
                }
            }
        }

        Err(last_error.unwrap_or_else(|| {
            CoreError::Network("达到最大重试次数后仍然失败".into())
        }))
    }

    /// 流式下载文件 (支持进度回调)
    pub async fn download_file<F>(
        &self,
        url: &str,
        dest: &std::path::Path,
        progress_callback: Option<F>,
    ) -> CoreResult<()>
    where
        F: Fn(u64, u64),
    {
        let _permit = self
            .concurrency
            .acquire()
            .await
            .map_err(|e| CoreError::Unknown(format!("信号量错误: {}", e)))?;

        // 确保父目录存在
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        // 流式下载
        let response = self.client.get(url).send().await?;
        if !response.status().is_success() {
            return Err(CoreError::Network(format!(
                "HTTP {}: {}",
                response.status().as_u16(),
                url
            )));
        }
        let total_size = response
            .content_length()
            .unwrap_or(0);

        let mut downloaded: u64 = 0;
        let mut file = tokio::fs::File::create(dest).await?;
        let stream = response.bytes_stream();

        use tokio_util::io::StreamReader;
        use futures_util::TryStreamExt;

        let stream_reader = StreamReader::new(
            stream.map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))
        );

        use tokio::io::AsyncWriteExt;
        let mut buf = [0u8; 8192];
        use tokio::io::AsyncReadExt;
        let mut reader = stream_reader;
        
        loop {
            let n = reader.read(&mut buf).await?;
            if n == 0 {
                break;
            }
            file.write_all(&buf[..n]).await?;
            downloaded += n as u64;

            if let Some(ref cb) = progress_callback {
                cb(downloaded, total_size);
            }
        }

        file.flush().await?;
        Ok(())
    }

    // ====================================================================
    //  URL 镜像辅助
    // ====================================================================

    /// 根据设置将 Mojang URL 转换为 BMCLAPI 镜像 URL
    pub fn resolve_url(&self, url: &str) -> String {
        if !self.bmclapi {
            return url.to_string();
        }

        // Mojang → BMCLAPI 镜像映射
        url.replace("https://launchermeta.mojang.com", "https://bmclapi2.bangbang93.com")
            .replace("https://resources.download.minecraft.net", "https://bmclapi2.bangbang93.com/assets")
            .replace("https://libraries.minecraft.net", "https://bmclapi2.bangbang93.com/libraries")
            .replace("https://piston-meta.mojang.com", "https://bmclapi2.bangbang93.com")
            .replace("https://piston-data.mojang.com", "https://bmclapi2.bangbang93.com")
            .replace("https://maven.minecraftforge.net", "https://bmclapi2.bangbang93.com/maven")
            .replace("https://maven.fabricmc.net", "https://bmclapi2.bangbang93.com/maven")
            .replace("https://maven.neoforged.net", "https://bmclapi2.bangbang93.com/maven")
            .replace("https://meta.fabricmc.net", "https://bmclapi2.bangbang93.com/fabric-meta")
    }

    /// 获取 GitHub 资源加速链接
    pub fn resolve_github_url(&self, url: &str) -> String {
        if !self.bmclapi {
            return url.to_string();
        }
        // 使用 ghfast.top 加速 GitHub 下载
        url.replace("https://github.com", "https://ghfast.top/https://github.com")
    }
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_url_resolve() {
        let client = HttpClient::new(true);
        assert_eq!(
            client.resolve_url("https://launchermeta.mojang.com/mc/game/version_manifest.json"),
            "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
        );
    }
}
