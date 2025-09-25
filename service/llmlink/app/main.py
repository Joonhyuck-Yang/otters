from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
import httpx
import os

# 설정
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./oters.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    ALLOWED_ORIGINS = ["http://localhost:3000", "https://your-frontend-domain.vercel.app"]
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # 로컬 Ollama API 설정
    LOCAL_OLLAMA_URL = os.getenv("LOCAL_OLLAMA_URL", "http://localhost:8003")

settings = Settings()

# 데이터베이스 설정
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 모델
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_uid = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    diary_entries = relationship("DiaryEntry", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")
    context_data = relationship("UserContextData", back_populates="user")

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(255), nullable=False, index=True)  # 구글 아이디
    diary = Column(Text, nullable=False)  # 사용자가 입력한 일기/일정
    date = Column(DateTime(timezone=True), nullable=False)  # 입력한 날짜/시간
    
    user = relationship("User", back_populates="diary_entries")

class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="chat_logs")

class UserContextData(Base):
    __tablename__ = "user_context_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data_type = Column(String(50), nullable=False)  # 'diary', 'note', 'memory'
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(String(500), nullable=True)  # 쉼표로 구분된 태그들
    importance_score = Column(Integer, default=1)  # 1-5 중요도
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="context_data")

# Pydantic 스키마
class GoogleAuthRequest(BaseModel):
    access_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class DiaryCreate(BaseModel):
    diary: str
    date: datetime

class DiaryResponse(BaseModel):
    id: int
    account_id: str
    diary: str
    date: datetime

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str

class ContextDataCreate(BaseModel):
    data_type: str
    title: Optional[str] = None
    content: str
    tags: Optional[str] = None
    importance_score: Optional[int] = 1

class ContextDataResponse(BaseModel):
    id: int
    data_type: str
    title: Optional[str]
    content: str
    tags: Optional[str]
    importance_score: int
    created_at: datetime
    updated_at: datetime

# 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except InvalidTokenError:
        return None

# 로컬 Ollama API 호출 함수
async def call_local_ollama_api(message: str, context: str = "") -> str:
    """로컬 Ollama API를 호출하여 응답 생성"""
    try:
        print(f"🤖 AI API 호출: {settings.LOCAL_OLLAMA_URL}")
        print(f"📝 사용자 메시지: {message[:50]}...")
        print(f"📚 컨텍스트: {context[:100] if context else '없음'}...")
        
        # 로컬 Ollama API 호출
        url = f"{settings.LOCAL_OLLAMA_URL}/api/chat"
        data = {
            "message": message,
            "context": context,
            "model": "llama2"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=60.0)
            print(f"📡 AI API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "죄송합니다. 응답을 생성할 수 없습니다.")
                print(f"✅ AI 응답: {ai_response[:100]}...")
                return ai_response
            else:
                print(f"❌ 로컬 Ollama API 오류: {response.status_code} - {response.text}")
                return "죄송합니다. 현재 AI 서비스에 문제가 있습니다."
                
    except httpx.ConnectError:
        print(f"❌ AI API 연결 실패: {settings.LOCAL_OLLAMA_URL}에 연결할 수 없습니다.")
        return "죄송합니다. AI 서비스에 연결할 수 없습니다. AI API 서비스가 실행 중인지 확인해주세요."
    except httpx.TimeoutException:
        print("⏰ AI API 응답 시간 초과")
        return "죄송합니다. AI 응답 시간이 초과되었습니다."
    except Exception as e:
        print(f"❌ 로컬 Ollama API 호출 실패: {e}")
        return "죄송합니다. 현재 AI 서비스에 문제가 있습니다."

# FastAPI 앱 생성
app = FastAPI(
    title="오터스 LLM Link Service",
    description="AI 개인 일기장 및 비서 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "오터스 LLM Link Service", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llmlink"}

# 인증 엔드포인트
@app.post("/api/auth/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth2 인증 처리"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={request.access_token}"
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            google_user = response.json()
            
        google_uid = google_user.get("id")
        email = google_user.get("email")
        name = google_user.get("name")
        
        if not all([google_uid, email, name]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information"
            )
        
        user = db.query(User).filter(User.google_uid == google_uid).first()
        if not user:
            user = User(
                google_uid=google_uid,
                email=email,
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"user_id": user.id}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """리프레시 토큰으로 새 액세스 토큰 발급"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    new_access_token = create_access_token(
        data={"user_id": user_id}
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=token,
        token_type="bearer"
    )

@app.get("/api/auth/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """현재 사용자 정보 조회"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at
    }

# 일기 엔드포인트
@app.post("/api/diary", response_model=DiaryResponse)
async def create_diary(
    diary: DiaryCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """일기 작성"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # 사용자 정보 가져오기
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    diary_entry = DiaryEntry(
        account_id=user.google_uid,  # 구글 아이디
        diary=diary.diary,           # 사용자가 입력한 일기/일정
        date=diary.date              # 입력한 날짜/시간
    )
    
    db.add(diary_entry)
    db.commit()
    db.refresh(diary_entry)
    
    # 일기를 컨텍스트 데이터에도 저장 (AI가 참조할 수 있도록)
    context_data = UserContextData(
        user_id=user_id,
        data_type="diary",
        title="일기",
        content=diary.diary,
        tags="일기,개인기록",
        importance_score=3
    )
    
    db.add(context_data)
    db.commit()
    
    return DiaryResponse(
        id=diary_entry.id,
        account_id=diary_entry.account_id,
        diary=diary_entry.diary,
        date=diary_entry.date
    )

@app.get("/api/diary", response_model=List[DiaryResponse])
async def get_diaries(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """사용자의 일기 목록 조회"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    diaries = db.query(DiaryEntry).filter(DiaryEntry.user_id == user_id).order_by(DiaryEntry.created_at.desc()).all()
    
    return [
        DiaryResponse(
            id=diary.id,
            title=diary.title,
            content=diary.content,
            created_at=diary.created_at
        )
        for diary in diaries
    ]

# 채팅 엔드포인트
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """AI와 채팅"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # 세션 ID 생성 (없는 경우)
    session_id = chat_message.session_id or f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 사용자 메시지 저장
    user_chat_log = ChatLog(
        user_id=user_id,
        session_id=session_id,
        role="user",
        message=chat_message.message
    )
    db.add(user_chat_log)
    
    try:
        # 사용자의 컨텍스트 데이터(일기 등) 가져오기
        context_data = db.query(UserContextData).filter(
            UserContextData.user_id == user_id
        ).order_by(UserContextData.importance_score.desc(), UserContextData.created_at.desc()).limit(5).all()
        
        # 컨텍스트 데이터를 문자열로 변환
        context_text = ""
        if context_data:
            print(f"📚 사용자 컨텍스트 데이터 {len(context_data)}개 발견")
            context_text = "\n".join([
                f"[{data.data_type}] {data.title or ''}: {data.content[:200]}..."
                for data in context_data
            ])
            print(f"📝 컨텍스트 요약: {context_text[:200]}...")
        else:
            print("📚 사용자 컨텍스트 데이터 없음")
        
        # 로컬 Ollama API 호출 (컨텍스트 포함)
        ai_message = await call_local_ollama_api(chat_message.message, context_text)
                
    except Exception as e:
        ai_message = f"AI 서비스 연결 오류: {str(e)}"
    
    # AI 응답 저장
    ai_chat_log = ChatLog(
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        message=ai_message
    )
    db.add(ai_chat_log)
    db.commit()
    
    return ChatResponse(
        message=ai_message,
        session_id=session_id
    )

@app.get("/api/chat/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """채팅 히스토리 조회"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    query = db.query(ChatLog).filter(ChatLog.user_id == user_id)
    if session_id:
        query = query.filter(ChatLog.session_id == session_id)
    
    chat_logs = query.order_by(ChatLog.created_at.asc()).all()
    
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "role": log.role,
            "message": log.message,
            "created_at": log.created_at
        }
        for log in chat_logs
    ]

@app.post("/api/chat/new-session")
async def create_new_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """새로운 채팅 세션 생성"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {"session_id": session_id, "message": "새로운 채팅 세션이 시작되었습니다."}

# 데이터베이스 테이블 생성 함수
def create_tables():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)

# 애플리케이션 시작 시 테이블 생성
if __name__ == "__main__":
    create_tables()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
