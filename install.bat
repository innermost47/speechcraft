@echo off
echo ======================================
echo        SpeechCraft Installation
echo ======================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in the PATH
    echo Please install Python 3.10 from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python detection...
python --version

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo [INFO] Python version detected: %PYTHON_VERSION%

echo.
echo [INFO] Creating virtual environment...
if exist env (
    echo [WARNING] The folder 'env' already exists
    set /p CHOICE="Do you want to delete and recreate it? (y/N): "
    if /i "!CHOICE!"=="y" (
        echo [INFO] Deleting old environment...
        rmdir /s /q env
    ) else (
        echo [INFO] Using existing environment...
        goto :activate
    )
)

python -m venv env
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

:activate
echo [INFO] Activating virtual environment...
call .\env\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [INFO] Updating pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Detecting CUDA support...
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Number of GPUs:', torch.cuda.device_count() if torch.cuda.is_available() else 0)" 2>nul
if errorlevel 1 (
    echo [WARNING] PyTorch is not yet installed, CUDA verification impossible
)

echo.
echo [INFO] Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo [ERROR] Failed to install PyTorch
    pause
    exit /b 1
)

echo.
echo [INFO] Installing dependencies from requirements.txt...
if not exist requirements.txt (
    echo [ERROR] The file requirements.txt was not found
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [INFO] Verifying installation...
python -c "import whisper; import torch; print('Whisper installed'); print('PyTorch installed'); print('CUDA available:', torch.cuda.is_available())"
if errorlevel 1 (
    echo [WARNING] Partial verification failed, but installation may work
)

echo.
if not exist .env (
    if exist env.example.txt (
        echo [INFO] Copying example configuration file...
        copy env.example.txt .env
        echo [WARNING] Please edit the .env file with your settings
    ) else (
        echo [WARNING] File env.example.txt not found
        echo [INFO] Create a .env file with your settings
    )
) else (
    echo [INFO] .env file already present
)

echo.
echo =======================================
echo        Installation complete!
echo =======================================
echo.
echo To start SpeechCraft:
echo 1. Activate the environment: .\env\Scripts\activate
echo 2. Start the server: python main.py
echo.
pause