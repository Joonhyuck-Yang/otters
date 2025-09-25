@echo off
echo 🚀 Ollama 서버 시작 중...
echo.

REM Ollama 서버 시작
echo 📡 Ollama 서버를 백그라운드에서 시작합니다...
start /B ollama serve

REM 서버가 시작될 때까지 대기
echo ⏳ 서버 시작을 기다리는 중...
timeout /t 5 /nobreak > nul

REM 서버 상태 확인
echo 🔍 Ollama 서버 상태 확인 중...
ollama list

echo.
echo ✅ Ollama 서버가 시작되었습니다!
echo 📡 서버 주소: http://localhost:11434
echo.
echo 💡 사용 가능한 명령어:
echo    - ollama list          : 모델 목록 확인
echo    - ollama pull llama2   : Llama2 모델 다운로드
echo    - ollama stop          : 서버 중지
echo.
echo 🎯 다음 단계: ai_api 서비스를 시작하세요!
echo    python app/main.py
echo.
pause
