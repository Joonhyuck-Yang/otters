# AI API 서비스

로컬 Ollama를 외부에서 접근할 수 있도록 하는 API 서비스입니다.

## 🚀 빠른 시작

### 1. Ollama 서버 시작
```bash
# Ollama 서버 시작
ollama serve

# 모델 다운로드 (필요한 경우)
ollama pull llama2
```

### 2. AI API 서비스 시작
```bash
# 의존성 설치
pip install -r requirements.txt

# 서비스 시작
python app/main.py
```

### 3. ngrok 터널링 (선택사항)
```bash
# ngrok으로 외부 접근 가능하게 만들기
ngrok http 11434
```

## 📡 API 엔드포인트

### 헬스 체크
```http
GET /api/health
```

### 모델 목록
```http
GET /api/models
```

### 채팅
```http
POST /api/chat
Content-Type: application/json

{
  "message": "안녕하세요!",
  "context": "사용자 컨텍스트 정보",
  "model": "llama2"
}
```

### 모델 다운로드
```http
POST /api/pull?model_name=llama2
```

## 🔧 설정

### 환경 변수
- `OLLAMA_HOST`: Ollama 서버 호스트 (기본값: localhost)
- `OLLAMA_PORT`: Ollama 서버 포트 (기본값: 11434)
- `DEFAULT_MODEL`: 기본 모델 (기본값: llama2)
- `API_PORT`: API 서버 포트 (기본값: 8003)

## 📁 폴더 구조

```
ai_api/
├── app/
│   └── main.py          # 메인 API 서비스
├── scripts/
│   ├── start_ollama.bat # Ollama 시작 스크립트
│   ├── start_ai_api.bat # AI API 시작 스크립트
│   └── start_ngrok.bat  # ngrok 시작 스크립트
├── config/
│   └── env.example      # 환경 설정 예시
├── requirements.txt     # Python 의존성
└── README.md           # 이 파일
```

## 🎯 사용 시나리오

1. **로컬 개발**: Ollama + AI API 서비스만 실행
2. **외부 접근**: Ollama + AI API 서비스 + ngrok 실행
3. **Render 배포**: ngrok URL을 Render 백엔드에서 사용

## ⚠️ 주의사항

- Ollama 서버가 먼저 실행되어야 합니다
- ngrok 사용 시 무료 계정 등록이 필요할 수 있습니다
- 모델 다운로드는 시간이 오래 걸릴 수 있습니다
