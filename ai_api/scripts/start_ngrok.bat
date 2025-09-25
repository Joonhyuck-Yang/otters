@echo off
echo 🌐 ngrok 터널링 시작 중...
echo.

REM ngrok이 설치되어 있는지 확인
where ngrok >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ ngrok이 설치되지 않았습니다.
    echo 💡 설치 방법:
    echo    1. https://ngrok.com/download 에서 다운로드
    echo    2. 또는 winget install Ngrok.Ngrok
    echo.
    pause
    exit /b 1
)

REM Ollama 서버가 실행 중인지 확인
echo 🔍 Ollama 서버 상태 확인 중...
curl -s http://localhost:11434/api/tags >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Ollama 서버가 실행되지 않았습니다.
    echo 💡 먼저 Ollama 서버를 시작하세요:
    echo    ollama serve
    echo.
    pause
    exit /b 1
)

echo ✅ Ollama 서버가 실행 중입니다.
echo.

REM ngrok 터널링 시작
echo 🚀 ngrok 터널링 시작...
echo 📡 로컬 포트: 11434 (Ollama)
echo 🌐 외부 URL: https://xxxxx.ngrok.io
echo.
echo 💡 ngrok 무료 계정이 필요한 경우:
echo    1. https://dashboard.ngrok.com/signup 에서 가입
echo    2. ngrok authtoken YOUR_TOKEN 명령어로 인증
echo.

ngrok http 11434

pause
