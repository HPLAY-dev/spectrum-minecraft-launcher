//! # Microsoft OAuth 认证
//!
//! 完整的 Microsoft OAuth 2.0 认证流程:
//!
//! 1. 启动本地 HTTP 服务器, 接收回调
//! 2. 打开浏览器引导用户登录
//! 3. 交换 Authorization Code → Access Token
//! 4. Xbox Live 认证 (XBL)
//! 5. XSTS 认证
//! 6. Minecraft 认证
//! 7. 获取玩家档案 (UUID + 用户名)
//!
//! 对应原 Python: `oauth_funcs.py` + `oauth_server.py`

use crate::http_client::HttpClient;
use crate::types::*;

use serde::{Deserialize, Serialize};
use tiny_http::{Server, Response};
use url::Url;
use std::time::Duration;

// ========================================================================
//  Microsoft OAuth 常量
// ========================================================================

/// Microsoft OAuth 端点
const MS_AUTHORIZE_URL: &str = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize";
const MS_TOKEN_URL: &str = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token";

/// Xbox Live 认证端点
const XBL_AUTH_URL: &str = "https://user.auth.xboxlive.com/user/authenticate";
const XSTS_AUTH_URL: &str = "https://xsts.auth.xboxlive.com/xsts/authorize";
const MC_AUTH_URL: &str = "https://api.minecraftservices.com/authentication/login_with_xbox";
const MC_PROFILE_URL: &str = "https://api.minecraftservices.com/minecraft/profile";

/// Azure Application Client ID (Spectrum Launcher)
const DEFAULT_CLIENT_ID: &str = "7000942a-0525-4e21-a817-faf950ab6bc4";

/// 与 mclauncher_core/oauth_server.py 保持一致
const REDIRECT_URI: &str = "http://localhost:8080/callback";
const AUTH_SCOPE: &str = "XboxLive.signin XboxLive.offline_access";
const TOKEN_SCOPE: &str = "XboxLive.signin offline_access";
const MC_ENTITLEMENTS_URL: &str = "https://api.minecraftservices.com/entitlements/mcstore";

const OAUTH_TIMEOUT_SECS: u64 = 120;

// ========================================================================
//  OAuth 数据结构
// ========================================================================

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct TokenResponse {
    access_token: String,
    #[serde(default)]
    refresh_token: String,
    #[serde(default)]
    expires_in: u64,
    #[serde(rename = "token_type")]
    token_type: String,
}

#[derive(Debug, Serialize)]
struct XboxLiveAuthRequest {
    #[serde(rename = "Properties")]
    properties: XboxLiveProperties,
    #[serde(rename = "RelyingParty")]
    relying_party: String,
    #[serde(rename = "TokenType")]
    token_type: String,
}

#[derive(Debug, Serialize)]
struct XboxLiveProperties {
    #[serde(rename = "AuthMethod")]
    auth_method: String,
    #[serde(rename = "SiteName")]
    site_name: String,
    #[serde(rename = "RpsTicket")]
    rps_ticket: String,
}

#[derive(Debug, Deserialize)]
struct XboxLiveAuthResponse {
    #[serde(rename = "Token")]
    token: String,
    #[serde(rename = "DisplayClaims")]
    display_claims: DisplayClaims,
}

#[derive(Debug, Deserialize)]
struct DisplayClaims {
    xui: Vec<XuiClaim>,
}

#[derive(Debug, Deserialize)]
struct XuiClaim {
    uhs: String,
}

#[derive(Debug, Serialize)]
struct XstsAuthRequest {
    #[serde(rename = "Properties")]
    properties: XstsProperties,
    #[serde(rename = "RelyingParty")]
    relying_party: String,
    #[serde(rename = "TokenType")]
    token_type: String,
}

#[derive(Debug, Serialize)]
struct XstsProperties {
    #[serde(rename = "SandboxId")]
    sandbox_id: String,
    #[serde(rename = "UserTokens")]
    user_tokens: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct MinecraftAuthResponse {
    #[serde(rename = "access_token")]
    access_token: String,
}

#[derive(Debug, Deserialize)]
pub struct MinecraftProfile {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct EntitlementsResponse {
    #[serde(default)]
    items: Vec<serde_json::Value>,
}

// ========================================================================
//  OAuth 客户端
// ========================================================================

/// Microsoft OAuth 认证器
#[derive(Debug, Clone)]
pub struct OAuthClient {
    #[allow(dead_code)]
    client: HttpClient,
    client_id: String,
    redirect_port: u16,
}

impl OAuthClient {
    pub fn new(client: HttpClient, client_id: Option<String>) -> Self {
        Self {
            client,
            client_id: client_id.unwrap_or_else(|| DEFAULT_CLIENT_ID.into()),
            redirect_port: 8080,
        }
    }

    /// 设置回调端口
    pub fn with_port(mut self, port: u16) -> Self {
        self.redirect_port = port;
        self
    }

    // ====================================================================
    //  完整认证流程
    // ====================================================================

    /// 执行完整的 Microsoft OAuth 认证流程
    /// 这是一个阻塞调用, 应在异步上下文中使用
    pub async fn authenticate(&self) -> CoreResult<OAuthResult> {
        log::info!("Getting auth_code");
        let auth_code = self.start_auth_server().await?;

        log::info!("Getting access_token");
        let tokens = self.exchange_code(&auth_code).await?;

        log::info!("Getting xbl");
        let xbl_response = self.authenticate_xbl(&tokens.access_token).await?;

        log::info!("Getting xsts");
        let xsts_response = self.authenticate_xsts(&xbl_response.token).await?;

        log::info!("Getting mc_token");
        let mc_token = self.authenticate_minecraft(
            &xsts_response.display_claims.xui[0].uhs,
            &xsts_response.token,
        )
        .await?;

        log::info!("Finish");
        let (uuid, username) = self.get_mslogin_uuid_name_from_token(&mc_token).await?;

        Ok(OAuthResult {
            access_token: mc_token,
            refresh_token: tokens.refresh_token,
            uuid,
            username,
        })
    }

    /// 刷新 Access Token
    pub async fn refresh_access_token(&self, refresh_token: &str) -> CoreResult<OAuthResult> {
        let params = [
            ("client_id", self.client_id.as_str()),
            ("refresh_token", refresh_token),
            ("grant_type", "refresh_token"),
            ("scope", TOKEN_SCOPE),
        ];

        let body = Self::form_urlencode(&params);

        let resp = reqwest::Client::new()
            .post(MS_TOKEN_URL)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .header("Accept", "application/json")
            .body(body)
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("Refresh Token 请求失败: {e}")))?;

        let status = resp.status();
        let text = resp
            .text()
            .await
            .map_err(|e| CoreError::OAuth(format!("读取响应失败: {e}")))?;

        if !status.is_success() {
            return Err(CoreError::OAuth(format!(
                "Refresh Token 失败 (HTTP {}): {}",
                status.as_u16(),
                text
            )));
        }

        let resp: TokenResponse = serde_json::from_str(&text)
            .map_err(|e| CoreError::OAuth(format!("Token 响应解析失败: {e}")))?;

        let ms_refresh = if resp.refresh_token.is_empty() {
            refresh_token.to_string()
        } else {
            resp.refresh_token
        };

        let xbl = self.authenticate_xbl(&resp.access_token).await?;
        let xsts = self.authenticate_xsts(&xbl.token).await?;
        let mc_token = self.authenticate_minecraft(
            &xsts.display_claims.xui[0].uhs,
            &xsts.token,
        )
        .await?;
        let (uuid, username) = self.get_mslogin_uuid_name_from_token(&mc_token).await?;

        Ok(OAuthResult {
            access_token: mc_token,
            refresh_token: ms_refresh,
            uuid,
            username,
        })
    }

    /// 用已有 Minecraft access token 获取 (uuid, username) — 对齐 Python is_owned()
    pub async fn get_profile_from_token(&self, mc_access_token: &str) -> CoreResult<(String, String)> {
        self.get_mslogin_uuid_name_from_token(mc_access_token).await
    }

    async fn get_mslogin_uuid_name_from_token(
        &self,
        mc_access_token: &str,
    ) -> CoreResult<(String, String)> {
        let (owned, profile) = self.check_ownership(mc_access_token).await?;
        if !owned {
            return Err(CoreError::OAuth(
                "No Minecraft license found or profile not available".into(),
            ));
        }
        log::info!("uuid={}", profile.id);
        log::info!("name={}", profile.name);
        Ok((profile.id, profile.name))
    }

    pub async fn check_ownership(
        &self,
        mc_access_token: &str,
    ) -> CoreResult<(bool, MinecraftProfile)> {
        let client = reqwest::Client::new();
        let headers = |req: reqwest::RequestBuilder| {
            req.header("Accept", "application/json")
                .bearer_auth(mc_access_token)
        };

        let entitlements_resp = headers(client.get(MC_ENTITLEMENTS_URL))
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("Entitlements 请求失败: {e}")))?;

        if !entitlements_resp.status().is_success() {
            return Ok((false, MinecraftProfile {
                id: String::new(),
                name: String::new(),
                error: Some(format!("HTTP {}", entitlements_resp.status())),
            }));
        }

        let entitlements: EntitlementsResponse = entitlements_resp
            .json()
            .await
            .map_err(|e| CoreError::OAuth(format!("Entitlements 解析失败: {e}")))?;

        let profile_resp = headers(client.get(MC_PROFILE_URL))
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("Profile 请求失败: {e}")))?;

        let profile_status = profile_resp.status();
        let profile: MinecraftProfile = if profile_status.is_success() {
            profile_resp
                .json()
                .await
                .unwrap_or(MinecraftProfile {
                    id: String::new(),
                    name: String::new(),
                    error: Some("parse_error".into()),
                })
        } else {
            MinecraftProfile {
                id: String::new(),
                name: String::new(),
                error: Some(format!("HTTP {}", profile_status)),
            }
        };

        let owned = !entitlements.items.is_empty()
            && profile_status.is_success()
            && profile.error.is_none()
            && !profile.id.is_empty();

        Ok((owned, profile))
    }

    // ====================================================================
    //  Step 1: 本地 HTTP 服务器 + Authorization Code
    // ====================================================================

    /// 启动本地 HTTP 服务器, 打开浏览器, 等待回调
    async fn start_auth_server(&self) -> CoreResult<String> {
        let auth_url = format!(
            "{}?client_id={}&response_type=code&redirect_uri={}&scope={}&response_mode=query",
            MS_AUTHORIZE_URL,
            self.client_id,
            urlencoding(REDIRECT_URI),
            urlencoding(AUTH_SCOPE),
        );

        let server = Server::http(format!("127.0.0.1:{}", self.redirect_port))
            .map_err(|e| CoreError::OAuth(format!("无法启动 HTTP 服务器: {}", e)))?;

        log::info!("Starting HTTP server on http://localhost:{}", self.redirect_port);
        log::info!("Opening browser for authentication: {}", auth_url);

        if let Err(e) = webbrowser::open(&auth_url) {
            log::warn!("无法自动打开浏览器: {}", e);
            log::info!("请手动访问: {}", auth_url);
        }

        log::info!(
            "Waiting for authentication... (timeout: {} seconds)",
            OAUTH_TIMEOUT_SECS
        );

        let start = std::time::Instant::now();
        let timeout = Duration::from_secs(OAUTH_TIMEOUT_SECS);

        loop {
            if start.elapsed() > timeout {
                return Err(CoreError::OAuth("Authentication timeout".into()));
            }

            match server.recv_timeout(Duration::from_secs(1)) {
                Ok(Some(request)) => {
                    let url = request.url().to_string();
                    log::debug!("收到请求: {}", url);

                    if url.starts_with("/callback") {
                        // 解析 Authorization Code
                        match self.parse_auth_code(&url) {
                            Ok(code) => {
                                log::info!("Auth Code Received: {}", code);
                                let response = Response::from_string(
                                    "<h1>Authentication Successful!</h1><p>You can close this window.</p>"
                                ).with_status_code(200);
                                let _ = request.respond(response);

                                return Ok(code);
                            }
                            Err(e) => {
                                let response = Response::from_string(
                                    format!("<html><body><h1>❌ 认证失败</h1><p>{}</p></body></html>", e)
                                ).with_status_code(400);
                                let _ = request.respond(response);
                                return Err(CoreError::OAuth(e));
                            }
                        }
                    } else {
                        // 其他请求, 返回 404
                        let response = Response::from_string("Not Found").with_status_code(404);
                        let _ = request.respond(response);
                    }
                }
                Ok(None) => continue, // 超时, 继续循环
                Err(e) => {
                    log::error!("HTTP 服务器错误: {}", e);
                    continue;
                }
            }
        }
    }

    /// 从回调 URL 中解析 Authorization Code
    fn parse_auth_code(&self, url: &str) -> Result<String, String> {
        let full_url = format!("http://localhost:{}{}", self.redirect_port, url);
        let parsed = Url::parse(&full_url).map_err(|e| format!("URL 解析失败: {}", e))?;

        // 检查是否包含错误
        if let Some(error) = parsed.query_pairs().find(|(k, _)| k == "error") {
            let desc = parsed.query_pairs()
                .find(|(k, _)| k == "error_description")
                .map(|(_, v)| v.to_string())
                .unwrap_or_default();
            return Err(format!("OAuth 错误: {} - {}", error.1, desc));
        }

        // 提取 code
        parsed.query_pairs()
            .find(|(k, _)| k == "code")
            .map(|(_, v)| v.to_string())
            .ok_or_else(|| "未找到 Authorization Code".into())
    }

    // ====================================================================
    //  Step 2: 交换 Code → Token
    // ====================================================================

    async fn exchange_code(&self, code: &str) -> CoreResult<TokenResponse> {
        let params = [
            ("client_id", self.client_id.as_str()),
            ("code", code),
            ("redirect_uri", REDIRECT_URI),
            ("grant_type", "authorization_code"),
            ("scope", TOKEN_SCOPE),
        ];

        let body = Self::form_urlencode(&params);

        let resp = reqwest::Client::new()
            .post(MS_TOKEN_URL)
            .header("Content-Type", "application/x-www-form-urlencoded")
            .header("Accept", "application/json")
            .body(body)
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("Token 请求失败: {}", e)))?;

        let status = resp.status();
        let text = resp.text().await
            .map_err(|e| CoreError::OAuth(format!("读取响应失败: {}", e)))?;

        if !status.is_success() {
            return Err(CoreError::OAuth(format!(
                "Token 交换失败 (HTTP {}): {}",
                status.as_u16(),
                text
            )));
        }

        serde_json::from_str(&text)
            .map_err(|e| CoreError::OAuth(format!("Token 响应解析失败: {}", e)))
    }

    // ====================================================================
    //  Step 3-5: Xbox Live → XSTS → Minecraft 认证链
    // ====================================================================

    async fn authenticate_xbl(&self, access_token: &str) -> CoreResult<XboxLiveAuthResponse> {
        let request = XboxLiveAuthRequest {
            properties: XboxLiveProperties {
                auth_method: "RPS".into(),
                site_name: "user.auth.xboxlive.com".into(),
                rps_ticket: format!("d={}", access_token),
            },
            relying_party: "http://auth.xboxlive.com".into(),
            token_type: "JWT".into(),
        };

        let client = reqwest::Client::new();
        let resp = client
            .post(XBL_AUTH_URL)
            .json(&request)
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .header("x-xbl-contract-version", "1")
            .timeout(Duration::from_secs(30))
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("XBL 认证失败: {}", e)))?;

        if !resp.status().is_success() {
            let text = resp.text().await.unwrap_or_default();
            return Err(CoreError::OAuth(format!("XBL 认证失败: {}", text)));
        }

        resp.json::<XboxLiveAuthResponse>()
            .await
            .map_err(|e| CoreError::OAuth(format!("XBL 响应解析失败: {}", e)))
    }

    async fn authenticate_xsts(&self, xbl_token: &str) -> CoreResult<XboxLiveAuthResponse> {
        let request = XstsAuthRequest {
            properties: XstsProperties {
                sandbox_id: "RETAIL".into(),
                user_tokens: vec![xbl_token.to_string()],
            },
            relying_party: "rp://api.minecraftservices.com/".into(),
            token_type: "JWT".into(),
        };

        let client = reqwest::Client::new();
        let resp = client
            .post(XSTS_AUTH_URL)
            .json(&request)
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .header("x-xbl-contract-version", "1")
            .send()
            .await
            .map_err(|e| CoreError::OAuth(format!("XSTS 认证失败: {}", e)))?;

        if !resp.status().is_success() {
            let status = resp.status().as_u16();
            let text = resp.text().await.unwrap_or_default();

            if status == 401 {
                return Err(CoreError::OAuth(
                    "XSTS 认证失败 (401)：该账户可能没有 Minecraft 正版授权，或者需要家长同意。".into()
                ));
            }

            return Err(CoreError::OAuth(format!("XSTS 认证失败 ({}): {}", status, text)));
        }

        resp.json::<XboxLiveAuthResponse>()
            .await
            .map_err(|e| CoreError::OAuth(format!("XSTS 响应解析失败: {}", e)))
    }

    async fn authenticate_minecraft(
        &self,
        user_hash: &str,
        xsts_token: &str,
    ) -> CoreResult<String> {
        let identity_token = format!("XBL3.0 x={};{}", user_hash, xsts_token);
        let body = serde_json::json!({ "identityToken": identity_token });

        Self::post_json_with_retry(
            MC_AUTH_URL,
            &body,
            &[],
            "Minecraft 认证失败",
            |resp| async move {
                if !resp.status().is_success() {
                    let text = resp.text().await.unwrap_or_default();
                    return Err(CoreError::OAuth(format!("Minecraft 认证失败: {}", text)));
                }

                let auth_resp: MinecraftAuthResponse = resp.json().await.map_err(|e| {
                    CoreError::OAuth(format!("Minecraft 认证响应解析失败: {}", e))
                })?;

                Ok(auth_resp.access_token)
            },
        )
        .await
    }

    // ====================================================================
    //  辅助方法
    // ====================================================================

    fn http_client() -> reqwest::Client {
        reqwest::Client::builder()
            .user_agent(format!(
                "SpectrumLauncher/{} ({})",
                env!("CARGO_PKG_VERSION", "0.1.0"),
                std::env::consts::OS
            ))
            .timeout(Duration::from_secs(60))
            .connect_timeout(Duration::from_secs(30))
            .tcp_keepalive(Some(Duration::from_secs(60)))
            .build()
            .unwrap_or_else(|_| reqwest::Client::new())
    }

    async fn post_json_with_retry<T, F, Fut>(
        url: &str,
        body: &serde_json::Value,
        extra_headers: &[(&str, &str)],
        error_label: &str,
        parser: F,
    ) -> CoreResult<T>
    where
        F: Fn(reqwest::Response) -> Fut,
        Fut: std::future::Future<Output = CoreResult<T>>,
    {
        let client = Self::http_client();
        let mut last_error = None;

        for attempt in 0..3 {
            if attempt > 0 {
                tokio::time::sleep(Duration::from_millis(500 * 2u64.pow(attempt - 1))).await;
                log::warn!("重试 {} [{}/{}]: {}", error_label, attempt + 1, 3, url);
            }

            let mut req = client
                .post(url)
                .json(body)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json");
            for (key, value) in extra_headers {
                req = req.header(*key, *value);
            }

            match req.send().await {
                Ok(resp) => match parser(resp).await {
                    Ok(value) => return Ok(value),
                    Err(err) => last_error = Some(err),
                },
                Err(err) => {
                    last_error = Some(CoreError::OAuth(format!(
                        "{}: {}（请检查网络/VPN 是否能访问 api.minecraftservices.com）",
                        error_label, err
                    )));
                }
            }
        }

        Err(last_error.unwrap_or_else(|| {
            CoreError::OAuth(format!("{}: 达到最大重试次数", error_label))
        }))
    }

    fn form_urlencode(params: &[(&str, &str)]) -> String {
        params.iter()
            .map(|(k, v)| format!("{}={}", urlencoding(k), urlencoding(v)))
            .collect::<Vec<_>>()
            .join("&")
    }
}

/// 简单的 URL 编码
fn urlencoding(s: &str) -> String {
    s.as_bytes().iter().map(|&c| match c {
        b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => (c as char).to_string(),
        b' ' => "%20".into(),
        _ => format!("%{:02X}", c),
    }).collect::<String>()
}

// ========================================================================
//  测试
// ========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_urlencoding() {
        assert_eq!(urlencoding("hello world"), "hello%20world");
        assert_eq!(urlencoding("a/b"), "a%2Fb");
    }

    #[test]
    fn test_parse_auth_code() {
        let client = OAuthClient::new(
            HttpClient::new(false),
            Some("test-client-id".into()),
        );

        // 模拟回调 URL
        let url = "/callback?code=abc123&state=test";
        let code = client.parse_auth_code(url);
        assert!(code.is_ok());
        assert_eq!(code.unwrap(), "abc123");
    }

    #[test]
    fn test_parse_auth_code_with_error() {
        let client = OAuthClient::new(
            HttpClient::new(false),
            Some("test-client-id".into()),
        );

        let url = "/callback?error=access_denied&error_description=User+cancelled";
        let result = client.parse_auth_code(url);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("access_denied"));
    }

    #[test]
    fn test_oauth_constants_match_python() {
        assert_eq!(REDIRECT_URI, "http://localhost:8080/callback");
        assert_eq!(AUTH_SCOPE, "XboxLive.signin XboxLive.offline_access");
        assert_eq!(TOKEN_SCOPE, "XboxLive.signin offline_access");
    }
}
