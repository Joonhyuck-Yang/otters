"""
게이트웨이 구글 인증 서비스
- 프론트엔드에서 오는 구글 로그인 요청을 받아서 처리
- 구글 OAuth2 토큰 검증 및 사용자 정보 조회
- JWT 토큰 발급 및 리다이렉트
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import os
import uvicorn
from typing import Optional

# 설정
class Settings:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    LLMLINK_SERVICE_URL = os.getenv("LLMLINK_SERVICE_URL", "http://localhost:8000")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_ORIGINS = ["http://localhost:3000", "https://otters-gpynyvem1-joonhyuck-yangs-projects.vercel.app"]

settings = Settings()

# FastAPI 앱 생성
app = FastAPI(
    title="오터스 게이트웨이 - 구글 인증",
    description="구글 OAuth2 인증 게이트웨이 서비스",
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

# Pydantic 모델
class GoogleAuthRequest(BaseModel):
    access_token: str

class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    redirect_url: Optional[str] = None
    user_info: Optional[GoogleUserInfo] = None

# 기본 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "오터스 게이트웨이 - 구글 인증 서비스",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth/google",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gateway-google-auth"}

# 구글 인증 엔드포인트
@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """구글 OAuth2 토큰 검증 및 사용자 인증"""
    try:
        print(f"🔐 구글 인증 요청 받음")
        
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
        
        # 사용자 정보 파싱
        user_info = GoogleUserInfo(
            id=google_user.get("id"),
            email=google_user.get("email"),
            name=google_user.get("name"),
            picture=google_user.get("picture")
        )
        
        # LLM Link 서비스로 사용자 정보 전달하여 JWT 토큰 발급
        try:
            async with httpx.AsyncClient() as client:
                llm_response = await client.post(
                    f"{settings.LLMLINK_SERVICE_URL}/api/auth/google",
                    json={"access_token": request.access_token},
                    timeout=10.0
                )
                
                if llm_response.status_code == 200:
                    llm_data = llm_response.json()
                    print(f"✅ LLM 서비스에서 JWT 토큰 발급 성공")
                    
                    # 프론트엔드로 리다이렉트 (토큰 포함)
                    redirect_url = f"{settings.FRONTEND_URL}/chat?token={llm_data.get('access_token')}"
                    
                    return AuthResponse(
                        success=True,
                        message="로그인 성공",
                        redirect_url=redirect_url,
                        user_info=user_info
                    )
                else:
                    print(f"❌ LLM 서비스 오류: {llm_response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user session"
                    )
                    
        except httpx.ConnectError:
            print(f"❌ LLM 서비스 연결 실패: {settings.LLMLINK_SERVICE_URL}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service unavailable"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 구글 인증 처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

# 구글 로그인 페이지 리다이렉트
@app.get("/api/auth/google/login")
async def google_login_redirect():
    """구글 로그인 페이지로 리다이렉트"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.FRONTEND_URL}/auth/callback&"
        f"scope=openid email profile&"
        f"response_type=code"
    )
    
    return RedirectResponse(url=google_auth_url)

# 구글 콜백 처리
@app.get("/api/auth/google/callback")
async def google_callback(code: str):
    """구글 OAuth2 콜백 처리"""
    try:
        # 구글에서 액세스 토큰 교환
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{settings.FRONTEND_URL}/auth/callback"
                },
                timeout=10.0
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received"
                )
        
        # 구글 인증 처리
        auth_request = GoogleAuthRequest(access_token=access_token)
        auth_response = await google_auth(auth_request)
        
        if auth_response.success:
            return RedirectResponse(url=auth_response.redirect_url)
        else:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=auth_failed")
            
    except Exception as e:
        print(f"❌ 구글 콜백 처리 실패: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=callback_failed")

if __name__ == "__main__":
    print("🚀 오터스 게이트웨이 - 구글 인증 서비스 시작")
    print(f"📡 프론트엔드 URL: {settings.FRONTEND_URL}")
    print(f"🔗 LLM 서비스 URL: {settings.LLMLINK_SERVICE_URL}")
    print("📋 사용 가능한 엔드포인트:")
    print("   - POST /api/auth/google     : 구글 토큰 검증")
    print("   - GET  /api/auth/google/login : 구글 로그인 리다이렉트")
    print("   - GET  /api/auth/google/callback : 구글 콜백 처리")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
