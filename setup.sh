#!/usr/bin/env bash

set -e

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Ensuring model directory exists..."
if [ ! -d "model" ]; then
  echo "Model not found, downloading..."
  wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
  unzip vosk-model-small-ru-0.22.zip
  mv vosk-model-small-ru-0.22 model
else
  echo "Model already exists, skipping download."
fi

echo "Setting up environment variables..."
export LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:$LD_LIBRARY_PATH
export PATH="$PWD/venv/bin:$PATH"
export PYTHONPATH="$PWD/venv/lib/python3.10/site-packages:$PYTHONPATH"

echo "Setup complete!"
echo "Run 'source venv/bin/activate' to activate the environment."
