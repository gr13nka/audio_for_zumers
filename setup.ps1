# === Add a folder for videos ===
New-Item -Path $pwd -Name "videos" -ItemType "directory"

# === Install Python ===
Write-Host "Installing Python..."
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe" -OutFile "python-installer.exe"
Start-Process -FilePath "python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Remove-Item -Force "python-installer.exe"

# === Install and update pip ===
Write-Host "Installing pip dependencies..."
python -m ensurepip --upgrade
python -m pip install --upgrade pip

# === Create a virtual environment ===
Write-Host "Creating a virtual environment..."
python -m venv venv

# Check if venv exists
if (-Not (Test-Path "venv")) {
    Write-Error "Error: Virtual environment was not created. Please check Python installation."
    exit 1
}
# Activate the virtual environment
Write-Host "Activating virtual environment..."
Set-Location -Path (Join-Path $PSScriptRoot "venv\Scripts")
.\Activate.ps1

# Return to the project root
Set-Location -Path $PSScriptRoot

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Installation complete!"

# === Install FFmpeg ===
Write-Host "Downloading FFmpeg..."
$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$ffmpegZip = "ffmpeg.zip"
$ffmpegDir = "ffmpeg"

# Check if the file was successfully downloaded
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -ErrorAction Stop
if (-Not (Test-Path $ffmpegZip)) {
    Write-Error "Error: Failed to download FFmpeg. Check your internet connection."
    exit 1
}

# Extract the archive
Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegDir -Force

# Delete the zip file after extraction
Remove-Item -Force $ffmpegZip
Write-Host "FFmpeg installed successfully."

# === Download the Vosk model ===
Write-Host "Downloading Vosk model..."
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip" -OutFile "vosk-model.zip"
Expand-Archive -Path "vosk-model.zip" -DestinationPath "model" -Force
Remove-Item -Force "vosk-model.zip"

Write-Host "Setup complete!"
