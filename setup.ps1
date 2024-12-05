# === Добавим папку для видео ===
New-Item -Path $pwd -Name "videos" -ItemType "directory"
# === allow local scripts
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# === Установка Python ===
Write-Host "Установка Python..."
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe" -OutFile "python-installer.exe"
Start-Process -FilePath "python-installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Remove-Item -Force "python-installer.exe"

# === Установка pip и обновление ===
Write-Host "Установка зависимостей pip..."
python -m ensurepip --upgrade
python -m pip install --upgrade pip

# === Создание виртуального окружения ===
Write-Host "Создание виртуального окружения..."
python -m venv venv

# Проверяем, существует ли venv
if (-Not (Test-Path "venv")) {
    Write-Error "Ошибка: виртуальное окружение не было создано. Проверьте установку Python."
    exit 1
}
# Активируем виртуальное окружение
Write-Host "Активация виртуального окружения..."
Set-Location -Path (Join-Path $PSScriptRoot "venv\Scripts")
.\Activate.ps1

# Возвращаемся в корень проекта
Set-Location -Path $PSScriptRoot

# Установка зависимостей
Write-Host "Установка зависимостей из requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Установка завершена!"

# === Установка FFmpeg ===
Write-Host "Скачивание FFmpeg..."
$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$ffmpegZip = "ffmpeg.zip"
$ffmpegDir = "ffmpeg"

# Проверяем, был ли файл успешно скачан
Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -ErrorAction Stop
if (-Not (Test-Path $ffmpegZip)) {
    Write-Error "Ошибка: не удалось скачать FFmpeg. Проверьте соединение с интернетом."
    exit 1
}

# Распаковываем архив
Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegDir -Force

# Удаляем zip файл после распаковки
Remove-Item -Force $ffmpegZip
Write-Host "FFmpeg успешно установлен."


# === Скачивание модели Vosk ===
Write-Host "Скачивание модели Vosk..."
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip" -OutFile "vosk-model.zip"
Expand-Archive -Path "vosk-model.zip" -DestinationPath "model" -Force
Remove-Item -Force "vosk-model.zip"

Write-Host "Установка завершена!"
