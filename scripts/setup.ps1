# Prepara o ambiente de desenvolvimento do minuta.io.
# Uso (na raiz do repositório):  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "== Motor Python (engine/.venv)"
$engine = Join-Path $root "engine"
$venvPython = Join-Path $engine ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    py -3.12 -m venv (Join-Path $engine ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar o ambiente Python (é necessário Python 3.12)." }
}
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -e "$engine[dev]" --quiet
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependências do motor." }

Write-Host "== Interface (apps/desktop)"
Push-Location (Join-Path $root "apps\desktop")
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "Falha no npm install." }
} finally {
    Pop-Location
}

Write-Host "== Modelo de português do Tesseract"
$tessdata = Join-Path $env:LOCALAPPDATA "minuta.io\tessdata"
New-Item -ItemType Directory -Force $tessdata | Out-Null
$installed = "C:\Program Files\Tesseract-OCR\tessdata"
foreach ($lang in "eng", "osd") {
    $target = Join-Path $tessdata "$lang.traineddata"
    if (-not (Test-Path $target) -and (Test-Path "$installed\$lang.traineddata")) {
        Copy-Item "$installed\$lang.traineddata" $target
    }
}
$por = Join-Path $tessdata "por.traineddata"
if (-not (Test-Path $por)) {
    Invoke-WebRequest -UseBasicParsing `
        "https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/por.traineddata" `
        -OutFile $por
}

Write-Host "Pronto. Para arrancar a app: cd apps\desktop; npm run tauri dev"
