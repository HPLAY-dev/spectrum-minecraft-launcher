//! 深度合并 version JSON（Forge/NeoForge 安装后合并原版依赖）

use crate::types::*;
use serde_json::Value;

/// 合并 ModLoader 与原版 version JSON，libraries 去重合并
pub fn merge_version_json(loader: &VersionJson, vanilla: &VersionJson) -> CoreResult<VersionJson> {
    let loader_v: Value = serde_json::to_value(loader).map_err(CoreError::Json)?;
    let vanilla_v: Value = serde_json::to_value(vanilla).map_err(CoreError::Json)?;
    let mut merged = deep_merge(vanilla_v.clone(), loader_v.clone());
    if let Some(obj) = merged.as_object_mut() {
        obj.insert(
            "libraries".into(),
            merge_libraries(vanilla_v.get("libraries"), loader_v.get("libraries")),
        );
    }
    serde_json::from_value(merged).map_err(CoreError::Json)
}

fn merge_libraries(a: Option<&Value>, b: Option<&Value>) -> Value {
    let a_arr = a.and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let b_arr = b.and_then(|v| v.as_array()).cloned().unwrap_or_default();
    let merged = deep_merge_list(a_arr, b_arr);
    Value::Array(merged)
}

fn deep_merge(a: Value, b: Value) -> Value {
    match (a, b) {
        (Value::Object(mut ao), Value::Object(bo)) => {
            for (k, bv) in bo {
                ao.insert(
                    k.clone(),
                    if let Some(av) = ao.get(&k) {
                        deep_merge(av.clone(), bv)
                    } else {
                        bv
                    },
                );
            }
            Value::Object(ao)
        }
        (Value::Array(a_arr), Value::Array(b_arr)) => Value::Array(deep_merge_list(a_arr, b_arr)),
        (_, b) => b,
    }
}

fn deep_merge_list(a: Vec<Value>, b: Vec<Value>) -> Vec<Value> {
    let mut merged = b.clone();
    let mut seen = std::collections::HashSet::new();
    for item in &b {
        seen.insert(library_key(item));
    }
    for item in a {
        let key = library_key(&item);
        if seen.contains(&key) {
            if let Some(existing) = merged.iter_mut().find(|x| library_key(x) == key) {
                if let (Value::Object(ex), Value::Object(ni)) =
                    (existing.clone(), item.clone())
                {
                    *existing = deep_merge(Value::Object(ex), Value::Object(ni));
                }
            }
            continue;
        }
        merged.push(item);
        seen.insert(key);
    }
    merged
}

fn library_key(item: &Value) -> String {
    if let Some(name) = item.get("name").and_then(|v| v.as_str()) {
        name.to_string()
    } else {
        item.to_string()
    }
}
