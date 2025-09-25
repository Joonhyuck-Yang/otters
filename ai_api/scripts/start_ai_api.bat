@echo off
echo 🚀 AI API 서비스 시작 중...
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 🔧 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 의존성 설치
echo 📦 의존성 설치 중...
pip install -r requirements.txt

REM AI API 서비스 시작
echo 🌐 AI API 서비스 시작...
echo 📡 로컬 Ollama: http://localhost:11434
echo 🌐 API 서버: http://localhost:8003
echo.

python app/main.py

pause
