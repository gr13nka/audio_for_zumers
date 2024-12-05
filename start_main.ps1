# === Navigate to the script directory ===
Set-Location -Path $PSScriptRoot

# === Check if the virtual environment exists ===
if (-Not (Test-Path "venv")) {
    Write-Host "Error: Virtual environment 'venv' not found in the current directory." -ForegroundColor Red
    exit 1
}

# === Activate the virtual environment ===
$venvActivate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (-Not (Test-Path $venvActivate)) {
    Write-Host "Error: Virtual environment activation script not found." -ForegroundColor Red
    exit 1
}

Write-Host "Activating virtual environment..."
& $venvActivate

# === Run main.py ===
if (-Not (Test-Path "main.py")) {
    Write-Host "Error: main.py not found in the current directory." -ForegroundColor Red
    exit 1
}

Write-Host "Running main.py..."
python main.py

# === Deactivate the virtual environment ===
Write-Host "Execution complete. Deactivating virtual environment."
deactivate
