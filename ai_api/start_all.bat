@echo off
echo 🚀 AI API 서비스 전체 시작 스크립트
echo =====================================
echo.

echo 1️⃣ Ollama 서버 시작 중...
start /B ollama serve
echo ⏳ Ollama 서버 시작 대기 중...
timeout /t 3 /nobreak > nul

echo 2️⃣ Ollama 서버 상태 확인...
ollama list
if %errorlevel% neq 0 (
    echo ❌ Ollama 서버 시작 실패
    pause
    exit /b 1
)

echo 3️⃣ AI API 서비스 시작 중...
echo 📡 로컬 Ollama: http://localhost:11434
echo 🌐 API 서버: http://localhost:8003
echo.

REM AI API 서비스 시작
python app/main.py

pause
