//! Ligação ao motor Python por JSON-RPC 2.0 sobre stdin/stdout (uma mensagem por linha).
//!
//! Não é aberta nenhuma porta de rede: só este processo consegue falar com o motor. Se a
//! aplicação terminar, o stdin do motor fecha e o motor termina sozinho.

use std::collections::HashMap;
use std::fmt;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

use serde_json::{json, Value};
use tokio::sync::oneshot;

/// Tempo máximo de espera por uma resposta. O OCR de documentos longos terá limites próprios.
const CALL_TIMEOUT: Duration = Duration::from_secs(120);

type Pending = Arc<Mutex<HashMap<u64, oneshot::Sender<Value>>>>;

#[derive(Debug)]
pub enum EngineError {
    /// O motor não está a correr ou a ligação foi interrompida.
    Unavailable,
    /// O motor não respondeu dentro do tempo limite.
    Timeout,
    /// O motor respondeu com um erro JSON-RPC (mensagem pensada para o utilizador).
    Rpc { message: String },
}

impl fmt::Display for EngineError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EngineError::Unavailable => write!(f, "O motor de processamento não está disponível."),
            EngineError::Timeout => write!(f, "O motor de processamento não respondeu a tempo."),
            EngineError::Rpc { message } => write!(f, "{message}"),
        }
    }
}

pub struct Engine {
    child: Mutex<Child>,
    stdin: Mutex<ChildStdin>,
    pending: Pending,
    next_id: AtomicU64,
}

impl Engine {
    /// Arranca o motor e as threads que leem as suas respostas.
    pub fn spawn() -> Result<Self, String> {
        let mut command = engine_command()?;
        command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("PYTHONUTF8", "1")
            .env("PYTHONIOENCODING", "utf-8");

        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            command.creation_flags(CREATE_NO_WINDOW);
        }

        let mut child = command
            .spawn()
            .map_err(|_| "Não foi possível arrancar o motor de processamento.".to_string())?;

        let stdin = child.stdin.take().ok_or("Motor sem stdin.")?;
        let stdout = child.stdout.take().ok_or("Motor sem stdout.")?;
        let stderr = child.stderr.take().ok_or("Motor sem stderr.")?;

        let pending: Pending = Arc::default();
        spawn_reader(stdout, pending.clone());

        // O stderr tem de ser consumido para o motor não bloquear. Em desenvolvimento é
        // mostrado na consola; em produção é descartado (pode conter dados de tracebacks).
        thread::spawn(move || {
            for line in BufReader::new(stderr).lines().map_while(Result::ok) {
                if cfg!(debug_assertions) {
                    eprintln!("[engine] {line}");
                }
            }
        });

        Ok(Self {
            child: Mutex::new(child),
            stdin: Mutex::new(stdin),
            pending,
            next_id: AtomicU64::new(1),
        })
    }

    /// Envia um pedido ao motor e espera pela resposta.
    pub async fn call(&self, method: &str, params: Value) -> Result<Value, EngineError> {
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        let (sender, receiver) = oneshot::channel();
        self.pending.lock().unwrap().insert(id, sender);

        let request = json!({ "jsonrpc": "2.0", "id": id, "method": method, "params": params });
        let written = {
            let mut stdin = self.stdin.lock().unwrap();
            writeln!(stdin, "{request}").and_then(|_| stdin.flush())
        };
        if written.is_err() {
            self.pending.lock().unwrap().remove(&id);
            return Err(EngineError::Unavailable);
        }

        let response = match tokio::time::timeout(CALL_TIMEOUT, receiver).await {
            Ok(Ok(response)) => response,
            Ok(Err(_)) => return Err(EngineError::Unavailable),
            Err(_) => {
                self.pending.lock().unwrap().remove(&id);
                return Err(EngineError::Timeout);
            }
        };

        if let Some(error) = response.get("error") {
            return Err(EngineError::Rpc {
                message: error
                    .get("message")
                    .and_then(Value::as_str)
                    .unwrap_or("Erro do motor.")
                    .to_string(),
            });
        }
        Ok(response.get("result").cloned().unwrap_or(Value::Null))
    }

    /// Termina o motor (chamado quando a aplicação fecha).
    pub fn shutdown(&self) {
        if let Ok(mut child) = self.child.lock() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

/// Lê as respostas do motor e entrega cada uma ao pedido correspondente (pelo `id`).
fn spawn_reader(stdout: std::process::ChildStdout, pending: Pending) {
    thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            let Ok(message) = serde_json::from_str::<Value>(&line) else {
                continue;
            };
            let Some(id) = message.get("id").and_then(Value::as_u64) else {
                continue;
            };
            if let Some(sender) = pending.lock().unwrap().remove(&id) {
                let _ = sender.send(message);
            }
        }
        // O motor terminou: os pedidos em espera falham com `Unavailable`.
        pending.lock().unwrap().clear();
    });
}

/// Comando para arrancar o motor.
///
/// Em desenvolvimento usa o Python do ambiente `engine/.venv` (ou `MINUTA_PYTHON`).
/// O motor empacotado como executável (sidecar) será usado nas versões de distribuição.
fn engine_command() -> Result<Command, String> {
    if cfg!(debug_assertions) {
        let python = match std::env::var_os("MINUTA_PYTHON") {
            Some(path) => PathBuf::from(path),
            None => PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../../../engine/.venv/Scripts/python.exe"),
        };
        if !python.is_file() {
            return Err(
                "Ambiente Python do motor não encontrado. Corra scripts\\setup.ps1.".to_string()
            );
        }
        let mut command = Command::new(python);
        command.args(["-m", "minuta_engine"]);
        Ok(command)
    } else {
        Err("O motor empacotado ainda não está incluído nesta versão.".to_string())
    }
}
