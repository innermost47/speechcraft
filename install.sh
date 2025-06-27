#!/bin/bash

echo "======================================"
echo "        SpeechCraft Installation"
echo "======================================"
echo

if ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed or not in the PATH"
    echo "Please install Python 3.10 from your package manager"
    exit 1
fi

echo "[INFO] Python detection..."
PYTHON_VERSION=$(python --version)
echo "$PYTHON_VERSION"
echo

echo "[INFO] Creating virtual environment..."
if [ -d "env" ]; then
    echo "[WARNING] The folder 'env' already exists"
    read -p "Do you want to delete and recreate it? (y/N): " CHOICE
    if [[ "$CHOICE" =~ ^[Yy]$ ]]; then
        echo "[INFO] Deleting old environment..."
        rm -rf env
    else
        echo "[INFO] Using existing environment..."
        source ./env/bin/activate
        if [ $? -ne 0 ]; then
            echo "[ERROR] Failed to activate existing virtual environment"
            exit 1
        fi
        echo "[INFO] Virtual environment activated"
        goto_pip_update=true
    fi
fi

if [ "$goto_pip_update" != true ]; then
    python -m venv env
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi

    echo "[INFO] Activating virtual environment..."
    source ./env/bin/activate
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to activate virtual environment"
        exit 1
    fi
fi

echo "[INFO] Updating pip..."
python -m pip install --upgrade pip

echo
echo "[INFO] Detecting CUDA support..."
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Number of GPUs:', torch.cuda.device_count() if torch.cuda.is_available() else 0)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNING] PyTorch is not yet installed, CUDA verification impossible"
fi

echo
echo "[INFO] Installing PyTorch with CUDA support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install PyTorch"
    exit 1
fi

echo
echo "[INFO] Installing dependencies from requirements.txt..."
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] The file requirements.txt was not found"
    exit 1
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo
echo "[INFO] Verifying installation..."
python -c "import whisper; import torch; print('Whisper installed'); print('PyTorch installed'); print('CUDA available:', torch.cuda.is_available())"
if [ $? -ne 0 ]; then
    echo "[WARNING] Partial verification failed, but installation may work"
fi

echo
if [ ! -f ".env" ]; then
    if [ -f "env.example.txt" ]; then
        echo "[INFO] Copying example configuration file..."
        cp env.example.txt .env
        echo "[WARNING] Please edit the .env file with your settings"
    else
        echo "[WARNING] File env.example.txt not found"
        echo "[INFO] Create a .env file with your settings"
    fi
else
    echo "[INFO] .env file already present"
fi

echo
echo "======================================="
echo "        Installation complete!"
echo "======================================="
echo
echo "To start SpeechCraft:"
echo "1. Activate the environment: source ./env/bin/activate"
echo "2. Start the server: python main.py"
echo

chmod +x "$0"