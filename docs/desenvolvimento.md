# Desenvolvimento

## Pré-requisitos (Windows)

| Ferramenta | Instalação |
|---|---|
| Node.js 22+ | <https://nodejs.org> |
| Python 3.12 | `winget install Python.Python.3.12` |
| Rust (MSVC) | `winget install Rustlang.Rustup` |
| Visual Studio Build Tools (C++) | `winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"` |
| Tesseract OCR | `winget install UB-Mannheim.TesseractOCR` |
| Microsoft Word | Opcional; necessário para exportar PDF |

## Preparar o ambiente

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```

O script:

1. cria `engine/.venv` e instala o motor em modo editável (com dependências de desenvolvimento);
2. instala as dependências npm em `apps/desktop`;
3. coloca os modelos de idioma do Tesseract (incluindo `por`) em `%LOCALAPPDATA%\minuta.io\tessdata`.

## Correr a aplicação

```powershell
cd apps\desktop
npm run tauri dev
```

Em desenvolvimento, o Tauri arranca o motor com `engine/.venv/Scripts/python.exe -m minuta_engine`.
Para usar outro Python, definir `MINUTA_PYTHON`.

## Testes e verificações

```powershell
cd engine
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .

cd ..\apps\desktop
npm run typecheck

cd src-tauri
cargo check
```

## Arquitetura em resumo

- `apps/desktop/src` — interface React. Fala com o motor através de `src/engine/client.ts`.
- `apps/desktop/src-tauri` — processo principal. `src/engine.rs` arranca o motor e encaminha as
  chamadas JSON-RPC (stdin/stdout, sem portas de rede).
- `engine/src/minuta_engine` — motor Python. Novos métodos registam-se em `main.py` (`METHODS`).

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `MINUTA_PYTHON` | Python usado para arrancar o motor em desenvolvimento |
| `MINUTA_DATA_DIR` | Substitui `%LOCALAPPDATA%\minuta.io` (testes) |
| `MINUTA_TESSERACT` | Caminho alternativo para `tesseract.exe` |

## Regras

- Não versionar minutas reais, documentos de clientes nem bases de dados.
- Testes usam apenas dados sintéticos.
- Logs: nunca registar valores, nomes de ficheiros, caminhos ou excertos de texto.
