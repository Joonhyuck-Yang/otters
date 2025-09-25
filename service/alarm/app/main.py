from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
import httpx
import os
import asyncio
import schedule
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

# 설정
class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/oters")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    ALLOWED_ORIGINS = ["http://localhost:3000", "https://your-frontend-domain.vercel.app"]
    LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # 이메일 설정
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@oters.com")

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
    schedules = relationship("Schedule", back_populates="user")

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
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

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    is_completed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="schedules")

# Pydantic 스키마
class GoogleAuthRequest(BaseModel):
    access_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class DiaryCreate(BaseModel):
    title: str
    content: str

class DiaryResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str

class ScheduleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_time: datetime

class ScheduleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    scheduled_time: datetime
    is_completed: bool
    is_active: bool
    created_at: datetime

class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
    is_active: Optional[bool] = None

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
    except JWTError:
        return None

def get_user_id_from_token(token: str) -> Optional[int]:
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload.get("user_id")
    return None

# 스케줄러 설정
scheduler = AsyncIOScheduler()

# FastAPI 앱 생성
app = FastAPI(
    title="오터스 Alarm Service",
    description="AI 개인 일기장 및 알람 서비스",
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
    return {"message": "오터스 Alarm Service", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "alarm"}

# 이메일 알림 관련 함수들
async def send_email_notification(user_email: str, user_name: str, title: str, description: str):
    """이메일 알림 전송 함수"""
    try:
        # 이메일 내용 생성
        subject = f"🔔 오터스 알림: {title}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    🔔 오터스 알림
                </h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">{title}</h3>
                    {f'<p style="color: #666;">{description}</p>' if description else ''}
                </div>
                
                <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #2c3e50;">
                        안녕하세요, {user_name}님!<br>
                        설정하신 일정 시간이 되었습니다.
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:3000" 
                       style="background: #3498db; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        오터스로 이동
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    이 이메일은 오터스 AI 비서 서비스에서 자동으로 발송되었습니다.<br>
                    문의사항이 있으시면 고객지원팀에 연락해주세요.
                </p>
            </div>
        </body>
        </html>
        """
        
        # 이메일 전송
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = user_email
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # SMTP 서버 연결 및 전송
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"이메일 알림 전송 완료: {user_email} - {title}")
        
    except Exception as e:
        print(f"이메일 알림 전송 실패: {e}")

async def send_notification(user_id: int, schedule_id: int, title: str, description: str):
    """실제 알람 전송 함수 (이메일)"""
    try:
        # 사용자 정보 가져오기
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            
            if user and schedule:
                # 이메일 알림 전송
                await send_email_notification(
                    user.email, 
                    user.name, 
                    title, 
                    description
                )
                
                # 일정 완료 처리
                schedule.is_completed = True
                db.commit()
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"알람 전송 실패: {e}")

def schedule_notification(schedule_id: int, user_id: int, title: str, description: str, scheduled_time: datetime):
    """스케줄러에 알람 작업 추가"""
    scheduler.add_job(
        send_notification,
        trigger=DateTrigger(run_date=scheduled_time),
        args=[user_id, schedule_id, title, description],
        id=f"alarm_{schedule_id}",
        replace_existing=True
    )

# 스케줄링 엔드포인트
@app.post("/api/schedule", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """일정 생성 및 알람 설정"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # 일정 생성
    schedule_entry = Schedule(
        user_id=user_id,
        title=schedule.title,
        description=schedule.description,
        scheduled_time=schedule.scheduled_time
    )
    
    db.add(schedule_entry)
    db.commit()
    db.refresh(schedule_entry)
    
    # 알람 스케줄링
    schedule_notification(
        schedule_entry.id,
        user_id,
        schedule_entry.title,
        schedule_entry.description or "",
        schedule_entry.scheduled_time
    )
    
    return ScheduleResponse(
        id=schedule_entry.id,
        title=schedule_entry.title,
        description=schedule_entry.description,
        scheduled_time=schedule_entry.scheduled_time,
        is_completed=schedule_entry.is_completed,
        is_active=schedule_entry.is_active,
        created_at=schedule_entry.created_at
    )

@app.get("/api/schedule", response_model=List[ScheduleResponse])
async def get_schedules(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """사용자의 일정 목록 조회"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    schedules = db.query(Schedule).filter(Schedule.user_id == user_id).order_by(Schedule.scheduled_time.asc()).all()
    
    return [
        ScheduleResponse(
            id=schedule.id,
            title=schedule.title,
            description=schedule.description,
            scheduled_time=schedule.scheduled_time,
            is_completed=schedule.is_completed,
            is_active=schedule.is_active,
            created_at=schedule.created_at
        )
        for schedule in schedules
    ]

@app.put("/api/schedule/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """일정 수정"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # 업데이트할 필드들
    if schedule_update.title is not None:
        schedule.title = schedule_update.title
    if schedule_update.description is not None:
        schedule.description = schedule_update.description
    if schedule_update.scheduled_time is not None:
        schedule.scheduled_time = schedule_update.scheduled_time
    if schedule_update.is_completed is not None:
        schedule.is_completed = schedule_update.is_completed
    if schedule_update.is_active is not None:
        schedule.is_active = schedule_update.is_active
    
    db.commit()
    db.refresh(schedule)
    
    # 알람 시간이 변경된 경우 스케줄러 업데이트
    if schedule_update.scheduled_time is not None:
        scheduler.remove_job(f"alarm_{schedule_id}")
        if schedule.is_active:
            schedule_notification(
                schedule.id,
                user_id,
                schedule.title,
                schedule.description or "",
                schedule.scheduled_time
            )
    
    return ScheduleResponse(
        id=schedule.id,
        title=schedule.title,
        description=schedule.description,
        scheduled_time=schedule.scheduled_time,
        is_completed=schedule.is_completed,
        is_active=schedule.is_active,
        created_at=schedule.created_at
    )

@app.delete("/api/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """일정 삭제"""
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # 스케줄러에서 작업 제거
    try:
        scheduler.remove_job(f"alarm_{schedule_id}")
    except:
        pass  # 작업이 없어도 무시
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}

# 데이터베이스 테이블 생성 함수
def create_tables():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)

# 애플리케이션 시작 시 테이블 생성 및 스케줄러 시작
@app.on_event("startup")
async def startup_event():
    create_tables()
    scheduler.start()
    print("알람 서비스가 시작되었습니다.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("알람 서비스가 종료되었습니다.")

# 애플리케이션 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
