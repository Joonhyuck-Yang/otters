# 오터스 LLM Link Service

## 실행 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 변경
```

3. 데이터베이스 테이블 생성:
```bash
python -c "from app.main import engine, Base; Base.metadata.create_all(bind=engine)"
```

4. 서버 실행:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 엔드포인트

### 인증
- `POST /api/auth/google` - Google OAuth2 로그인
- `POST /api/auth/refresh` - 토큰 갱신
- `GET /api/auth/me` - 현재 사용자 정보

### 일기
- `POST /api/diary` - 일기 작성
- `GET /api/diary` - 일기 목록 조회

### 채팅
- `POST /api/chat` - AI와 채팅
- `GET /api/chat/history` - 채팅 히스토리 조회
- `POST /api/chat/new-session` - 새 채팅 세션 생성

## 환경 변수

- `DATABASE_URL`: PostgreSQL 연결 URL
- `SECRET_KEY`: JWT 서명용 비밀키
- `GOOGLE_CLIENT_ID`: Google OAuth2 클라이언트 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth2 클라이언트 시크릿
- `LLM_SERVICE_URL`: LLM 서비스 URL
- `ENVIRONMENT`: 환경 (development/production)
- `DEBUG`: 디버그 모드 (true/false)

