use std::path::PathBuf;

fn main() -> std::io::Result<()> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../src");
    let messages = root.join("openocean/messages");
    println!("cargo:rerun-if-changed={}", messages.display());

    let mut protos: Vec<PathBuf> = std::fs::read_dir(&messages)?
        .map(|entry| entry.map(|e| e.path()))
        .collect::<Result<_, _>>()?;
    protos.retain(|path| path.extension().is_some_and(|ext| ext == "proto"));
    protos.sort();

    prost_build::compile_protos(&protos, &[root])
}
