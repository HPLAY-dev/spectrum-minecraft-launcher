use pyo3::prelude::*;
use reqwest::Client;

use crate::download::DownloadEngine;

static HTTP: std::sync::OnceLock<Client> = std::sync::OnceLock::new();

fn http() -> &'static Client {
    HTTP.get_or_init(|| Client::builder().build().expect("http client"))
}

#[pyfunction]
#[pyo3(signature = (show_snapshot=false, show_release=true, bmclapi=true))]
fn get_version_list(
    py: Python<'_>,
    show_snapshot: bool,
    show_release: bool,
    bmclapi: bool,
) -> PyResult<Vec<String>> {
    py.allow_threads(|| {
        let rt = tokio::runtime::Runtime::new().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        rt.block_on(async {
            let engine = DownloadEngine::new(http().clone(), bmclapi);
            engine
                .get_version_list(show_snapshot, show_release)
                .await
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
        })
    })
}

#[pyfunction]
fn is_rust_core() -> bool {
    true
}

#[pymodule]
fn _mc_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_version_list, m)?)?;
    m.add_function(wrap_pyfunction!(is_rust_core, m)?)?;
    Ok(())
}
