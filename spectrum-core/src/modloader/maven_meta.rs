//! Maven metadata.xml 版本列表解析

use crate::http_client::HttpClient;
use crate::types::*;
use quick_xml::events::Event;
use quick_xml::Reader;

/// 从 `{base}/{artifact_path}/maven-metadata.xml` 读取 `<versions>` 列表（新→旧）
pub async fn fetch_maven_versions(
    client: &HttpClient,
    base: &str,
    artifact_path: &str,
    use_bmclapi_mirror: bool,
) -> CoreResult<Vec<String>> {
    let url = format!("{}/{}/maven-metadata.xml", base.trim_end_matches('/'), artifact_path);
    let resolved = if use_bmclapi_mirror {
        client.resolve_url(&url)
    } else {
        url
    };
    let xml = client.get_text(&resolved).await?;

    let mut reader = Reader::from_str(&xml);
    let mut buf = Vec::new();
    let mut in_versions = false;
    let mut versions = Vec::new();
    let mut current_text = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) if e.name().as_ref() == b"versions" => {
                in_versions = true;
            }
            Ok(Event::Text(ref e)) => {
                current_text = e.unescape().unwrap_or_default().to_string();
            }
            Ok(Event::End(ref e)) if e.name().as_ref() == b"version" && in_versions => {
                versions.push(current_text.clone());
            }
            Ok(Event::End(ref e)) if e.name().as_ref() == b"versions" => break,
            Ok(Event::Eof) => break,
            Err(e) => return Err(CoreError::Xml(format!("XML 解析错误: {e}"))),
            _ => {}
        }
        buf.clear();
    }

    versions.reverse();
    Ok(versions)
}
