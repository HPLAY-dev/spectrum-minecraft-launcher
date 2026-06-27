use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct CoreConfig {
    pub minecraft_dir: PathBuf,
    pub use_bmclapi: bool,
}

impl Default for CoreConfig {
    fn default() -> Self {
        Self {
            minecraft_dir: PathBuf::from(".minecraft"),
            use_bmclapi: true,
        }
    }
}
