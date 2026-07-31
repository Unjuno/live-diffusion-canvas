#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            start_packaged_runtime(app)?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Live Diffusion Canvas");
    app.run(|app: &tauri::AppHandle, event: tauri::RunEvent| {
        if let tauri::RunEvent::Exit = event {
            if let Some(process) = app.try_state::<RuntimeProcess>() {
                if let Ok(mut child) = process.child.lock() {
                    if let Some(child) = child.as_mut() {
                        let _ = child.kill();
                    }
                }
            }
        }
    });
}

use std::{
    fs,
    net::TcpStream,
    path::{Path, PathBuf},
    process::{Child, Command},
    sync::Mutex,
    time::Duration,
};
use tauri::Manager;

const RUNTIME_ADDRESS: &str = "127.0.0.1:8000";

struct RuntimeProcess {
    child: Mutex<Option<Child>>,
}

fn runtime_is_running() -> bool {
    TcpStream::connect_timeout(
        &RUNTIME_ADDRESS.parse().expect("valid runtime address"),
        Duration::from_millis(250),
    )
    .is_ok()
}

fn start_packaged_runtime(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    app.manage(RuntimeProcess {
        child: Mutex::new(None),
    });
    if runtime_is_running() {
        return Ok(());
    }

    let resource_dir = app.path().resource_dir()?;
    let runtime_root = unpack_runtime_resources(app, &resource_dir)?;
    let backend_dir = resource_dir.join("backend");
    if !backend_dir.join("app.py").exists() {
        eprintln!("Packaged runtime backend is not present; using the UI Mock Runtime.");
        return Ok(());
    }

    let python_candidates = [
        std::env::var_os("DIFFUSION_PYTHON").map(std::path::PathBuf::from),
        Some(runtime_root.join(".venv-real/bin/python")),
        Some(std::path::PathBuf::from("python3")),
    ];
    let python = python_candidates
        .into_iter()
        .flatten()
        .find(|candidate| candidate == std::path::Path::new("python3") || candidate.is_file());
    let Some(python) = python else {
        eprintln!("No Python runtime found; use the setup script before selecting TinySD.");
        return Ok(());
    };

    let bundled_model = runtime_root.join("models/segmind/tiny-sd");

    let mut command = Command::new(python);
    command
        .arg("-m")
        .arg("uvicorn")
        .arg("backend.app:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("8000")
        .current_dir(&resource_dir)
        .env("PYTHONPATH", &resource_dir)
        .env(
            "DIFFUSION_REAL",
            std::env::var("DIFFUSION_REAL").unwrap_or_else(|_| "1".into()),
        )
        .env(
            "DIFFUSION_MODEL",
            std::env::var_os("DIFFUSION_MODEL").unwrap_or_else(|| {
                if bundled_model.join("model_index.json").exists() {
                    bundled_model.into_os_string()
                } else {
                    "segmind/tiny-sd".into()
                }
            }),
        );

    match command.spawn() {
        Ok(child) => {
            if let Some(process) = app.try_state::<RuntimeProcess>() {
                *process
                    .child
                    .lock()
                    .map_err(|_| "runtime process lock poisoned")? = Some(child);
            }
            for _ in 0..60 {
                if runtime_is_running() {
                    eprintln!("Started packaged local diffusion runtime at {RUNTIME_ADDRESS}.");
                    return Ok(());
                }
                std::thread::sleep(Duration::from_millis(250));
            }
            if let Some(process) = app.try_state::<RuntimeProcess>() {
                if let Ok(mut child) = process.child.lock() {
                    if let Some(child) = child.as_mut() {
                        let _ = child.kill();
                    }
                    *child = None;
                }
            }
            eprintln!("Packaged diffusion runtime did not become ready at {RUNTIME_ADDRESS}.");
        }
        Err(error) => eprintln!("Could not start packaged runtime: {error}. Build the self-contained app with scripts/build-macos-full.sh."),
    }
    Ok(())
}

fn unpack_runtime_resources(
    app: &tauri::App,
    resource_dir: &Path,
) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let runtime_archive = resource_dir.join("real-runtime.tar.gz");
    let model_archive = resource_dir.join("tiny-sd-model.tar.gz");
    if !runtime_archive.exists() && !model_archive.exists() {
        return Ok(resource_dir.to_path_buf());
    }

    let root = app.path().app_data_dir()?.join("runtime-bundle");
    fs::create_dir_all(&root)?;
    let marker = root.join(".unpacked-v1");
    if !marker.exists() {
        if runtime_archive.exists() {
            extract_archive(&runtime_archive, &root)?;
        }
        if model_archive.exists() {
            extract_archive(&model_archive, &root)?;
        }
        fs::write(marker, b"v1")?;
    }
    Ok(root)
}

fn extract_archive(archive: &Path, destination: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let status = Command::new("tar")
        .arg("-xzf")
        .arg(archive)
        .arg("-C")
        .arg(destination)
        .status()?;
    if !status.success() {
        return Err(format!("Could not unpack runtime archive: {}", archive.display()).into());
    }
    Ok(())
}
