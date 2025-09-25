# 오터스 (Otters) - AI 개인 비서 서비스

오터스는 AI 기반의 개인 비서 서비스로, 일기 작성, 채팅, 스케줄링 및 알람 기능을 제공합니다.

## 🚀 주요 기능

- **AI 채팅**: 개인화된 AI 비서와의 대화
- **일기 작성**: 개인 일기 작성 및 관리
- **스케줄링**: 일정 관리 및 알람 설정
- **실시간 알람**: 설정된 시간에 푸시 알림

## 🏗️ 아키텍처

### MSA (Microservice Architecture)
- **Frontend**: React 기반 웹 애플리케이션
- **Gateway**: API 게이트웨이 (요청 라우팅)
- **Services**: 
  - `llmlink`: AI 채팅 및 일기 서비스
  - `alarm`: 스케줄링 및 알람 서비스

### 기술 스택
- **Backend**: FastAPI, Python
- **Frontend**: React, Styled Components
- **Database**: PostgreSQL
- **Authentication**: Google OAuth2
- **Scheduler**: APScheduler
- **LLM**: Ollama (로컬 실행)

## 📁 프로젝트 구조

```
오터스/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/       # React 컴포넌트
│   │   └── App.js
│   └── package.json
├── gateway/                  # API 게이트웨이
│   └── alaim/
├── service/                  # 마이크로서비스들
│   ├── llmlink/             # AI 채팅 및 일기 서비스
│   │   └── app/
│   │       └── main.py
│   └── alarm/               # 알람 및 스케줄링 서비스
│       └── app/
│           └── main.py
└── README.md
```

## 🚀 실행 방법

### 1. 백엔드 서비스 실행

```bash
# LLM Link 서비스 (포트 8000)
cd service/llmlink
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Alarm 서비스 (포트 8002)
cd service/alarm
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### 2. 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

### 3. Ollama 설정

```bash
# Ollama 설치 (Windows)
winget install Ollama.Ollama

# 모델 다운로드
ollama pull llama2
```

## 🔧 환경 설정

### 환경 변수
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/oters
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
LLM_SERVICE_URL=http://localhost:8001
```

## 📱 API 엔드포인트

### 인증
- `POST /api/auth/google` - Google OAuth2 로그인
- `POST /api/auth/refresh` - 토큰 갱신
- `GET /api/auth/me` - 사용자 정보 조회

### 채팅
- `POST /api/chat` - AI와 채팅
- `GET /api/chat/history` - 채팅 히스토리 조회
- `POST /api/chat/new-session` - 새 채팅 세션 생성

### 일기
- `POST /api/diary` - 일기 작성
- `GET /api/diary` - 일기 목록 조회

### 스케줄링
- `POST /api/schedule` - 일정 생성 및 알람 설정
- `GET /api/schedule` - 일정 목록 조회
- `PUT /api/schedule/{id}` - 일정 수정
- `DELETE /api/schedule/{id}` - 일정 삭제

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 링크: [https://github.com/your-username/otters](https://github.com/your-username/otters)