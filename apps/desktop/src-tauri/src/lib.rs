//! Processo principal do minuta.io.
//!
//! A camada Rust é propositadamente fina: arranca o motor Python, encaminha as chamadas da
//! interface para ele e controla as permissões da janela. A lógica de domínio vive no motor.

mod engine;

use std::sync::Arc;

use serde_json::Value;
use tauri::{Manager, RunEvent, State};

use engine::Engine;

/// Estado partilhado: o motor, ou a razão pela qual não foi possível arrancá-lo.
struct EngineState(Result<Arc<Engine>, String>);

/// Encaminha uma chamada JSON-RPC da interface para o motor Python.
#[tauri::command]
async fn engine_call(
    state: State<'_, EngineState>,
    method: String,
    params: Option<Value>,
) -> Result<Value, String> {
    let engine = state.0.as_ref().map_err(Clone::clone)?.clone();
    engine
        .call(&method, params.unwrap_or_else(|| Value::Object(Default::default())))
        .await
        .map_err(|error| error.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            app.manage(EngineState(Engine::spawn().map(Arc::new)));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![engine_call])
        .build(tauri::generate_context!())
        .expect("erro ao iniciar a aplicação");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            if let Some(state) = handle.try_state::<EngineState>() {
                if let Ok(engine) = &state.0 {
                    engine.shutdown();
                }
            }
        }
    });
}
