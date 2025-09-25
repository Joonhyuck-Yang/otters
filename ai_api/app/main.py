"""
로컬 Ollama API 서비스
- 로컬에서 실행되는 Ollama를 외부에서 접근할 수 있도록 하는 API 서비스
- ngrok을 통해 터널링하여 Render 백엔드에서 접근 가능
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from typing import Optional
import uvicorn

app = FastAPI(
    title="Ollama Local API",
    description="로컬 Ollama를 외부에서 접근할 수 있도록 하는 API 서비스",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    model: Optional[str] = "llama2"

class ChatResponse(BaseModel):
    response: str
    model: str
    success: bool

class HealthResponse(BaseModel):
    status: str
    ollama_status: str
    model: str

@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Ollama Local API Service",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health",
            "models": "/api/models"
        }
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 - Ollama 연결 상태 확인"""
    try:
        # Ollama 서버 상태 확인
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json()
                model_list = [model["name"] for model in models.get("models", [])]
                return HealthResponse(
                    status="healthy",
                    ollama_status="connected",
                    model=", ".join(model_list) if model_list else "no models"
                )
            else:
                return HealthResponse(
                    status="unhealthy",
                    ollama_status="disconnected",
                    model="unknown"
                )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            ollama_status=f"error: {str(e)}",
            model="unknown"
        )

@app.get("/api/models")
async def get_models():
    """사용 가능한 모델 목록 조회"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=500, detail="Ollama 서버에 연결할 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 실패: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_ollama(request: ChatRequest):
    """Ollama와 채팅"""
    try:
        # 프롬프트 구성
        if request.context:
            prompt = f"사용자 컨텍스트: {request.context}\n\n사용자 질문: {request.message}\n\n위 컨텍스트를 참고하여 친근하게 답변해주세요."
        else:
            prompt = request.message

        # Ollama API 호출
        ollama_payload = {
            "model": request.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=ollama_payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return ChatResponse(
                    response=result["message"]["content"],
                    model=request.model,
                    success=True
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ollama API 오류: {response.status_code} - {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama 응답 시간 초과")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 처리 실패: {str(e)}")

@app.post("/api/pull")
async def pull_model(model_name: str):
    """모델 다운로드"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:11434/api/pull",
                json={"name": model_name},
                timeout=300.0  # 모델 다운로드는 시간이 오래 걸릴 수 있음
            )
            
            if response.status_code == 200:
                return {"message": f"모델 {model_name} 다운로드 완료", "success": True}
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"모델 다운로드 실패: {response.status_code} - {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="모델 다운로드 시간 초과")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 다운로드 실패: {str(e)}")

if __name__ == "__main__":
    print("🚀 Ollama Local API Service 시작")
    print("📡 로컬 Ollama 서버: http://localhost:11434")
    print("🌐 API 서버: http://localhost:8003")
    print("📋 사용 가능한 엔드포인트:")
    print("   - GET  /api/health  : 헬스 체크")
    print("   - GET  /api/models  : 모델 목록")
    print("   - POST /api/chat    : 채팅")
    print("   - POST /api/pull    : 모델 다운로드")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
