use std::sync::Mutex;

use serde::Serialize;
use tauri::{AppHandle, Manager, RunEvent, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

const ENGINE_ADDR: &str = "127.0.0.1:14200";

/// The Go sidecar. We hold `child` for the app's lifetime: it owns the write
/// end of the engine's stdin, and the engine exits when that pipe closes.
struct Engine {
    token: String,
    child: Mutex<Option<CommandChild>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct EngineInfo {
    base_url: String,
    ws_url: String,
    token: String,
}

#[tauri::command]
fn engine_info(engine: State<'_, Engine>) -> EngineInfo {
    EngineInfo {
        base_url: format!("http://{ENGINE_ADDR}"),
        ws_url: format!("ws://{ENGINE_ADDR}"),
        token: engine.token.clone(),
    }
}

fn random_token() -> String {
    let mut buf = [0u8; 32];
    getrandom::fill(&mut buf).expect("OS random number generator unavailable");
    buf.iter().map(|b| format!("{b:02x}")).collect()
}

fn spawn_engine(app: &AppHandle, token: &str) -> Result<CommandChild, Box<dyn std::error::Error>> {
    let (mut rx, child) = app
        .shell()
        .sidecar("engine")?
        .env("FK_ENGINE_TOKEN", token)
        .env("FK_ENGINE_ADDR", ENGINE_ADDR)
        .spawn()?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[engine] {}", String::from_utf8_lossy(&line).trim_end())
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[engine] {}", String::from_utf8_lossy(&line).trim_end())
                }
                CommandEvent::Error(err) => eprintln!("[engine] error: {err}"),
                CommandEvent::Terminated(status) => {
                    eprintln!("[engine] exited (code {:?}, signal {:?})", status.code, status.signal);
                    break;
                }
                _ => {}
            }
        }
    });
    Ok(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let token = random_token();
            let child = spawn_engine(app.handle(), &token)?;
            app.manage(Engine {
                token,
                child: Mutex::new(Some(child)),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![engine_info])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                if let Some(child) = app.state::<Engine>().child.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}
