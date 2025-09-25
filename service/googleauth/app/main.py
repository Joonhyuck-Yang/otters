"""
서비스 단 구글 인증 서비스
- 게이트웨이에서 전달받은 구글 토큰을 검증
- 사용자 정보를 데이터베이스에 저장
- JWT 토큰 발급 및 반환
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import InvalidTokenError
import httpx
import os
import uvicorn

# 설정
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./oters.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    ALLOWED_ORIGINS = ["http://localhost:3000", "https://otters-gpynyvem1-joonhyuck-yangs-projects.vercel.app"]

settings = Settings()

# 데이터베이스 설정
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 모델
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    google_uid = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    picture = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Pydantic 스키마
class GoogleAuthRequest(BaseModel):
    access_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_info: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    google_uid: str
    email: str
    name: str
    picture: Optional[str]
    created_at: datetime

# 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT 토큰 생성 함수
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

# FastAPI 앱 생성
app = FastAPI(
    title="오터스 서비스 - 구글 인증",
    description="구글 OAuth2 인증 처리 서비스",
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
    return {
        "message": "오터스 서비스 - 구글 인증",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth/google",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "google-auth-service"}

# 구글 인증 엔드포인트
@app.post("/api/auth/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """구글 OAuth2 토큰 검증 및 사용자 인증"""
    try:
        print(f"🔐 구글 인증 요청 받음 (서비스)")
        
        # 구글 API로 사용자 정보 조회
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={request.access_token}",
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"❌ 구글 API 오류: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            google_user = response.json()
            print(f"✅ 구글 사용자 정보 조회 성공: {google_user.get('email')}")
        
        # 사용자 정보 추출
        google_uid = google_user.get("id")
        email = google_user.get("email")
        name = google_user.get("name")
        picture = google_user.get("picture")
        
        if not all([google_uid, email, name]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information"
            )
        
        # 데이터베이스에서 사용자 조회 또는 생성
        user = db.query(User).filter(User.google_uid == google_uid).first()
        if not user:
            user = User(
                google_uid=google_uid,
                email=email,
                name=name,
                picture=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ 새 사용자 생성: {user.email}")
        else:
            # 기존 사용자 정보 업데이트
            user.email = email
            user.name = name
            user.picture = picture
            db.commit()
            print(f"✅ 기존 사용자 정보 업데이트: {user.email}")
        
        # JWT 토큰 생성
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"user_id": user.id}
        )
        
        # 사용자 정보 반환
        user_info = {
            "id": user.id,
            "google_uid": user.google_uid,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at.isoformat()
        }
        
        print(f"✅ JWT 토큰 발급 완료: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_info=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 구글 인증 처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

# 토큰 검증 엔드포인트
@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str, db: Session = Depends(get_db)):
    """JWT 토큰 검증"""
    payload = verify_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "valid": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

# 데이터베이스 테이블 생성 함수
def create_tables():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("🚀 오터스 서비스 - 구글 인증 시작")
    print(f"📡 데이터베이스: {settings.DATABASE_URL}")
    print("📋 사용 가능한 엔드포인트:")
    print("   - POST /api/auth/google : 구글 토큰 검증 및 JWT 발급")
    print("   - GET  /api/auth/verify : JWT 토큰 검증")
    
    create_tables()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )