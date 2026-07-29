from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, status
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from app.config import Settings, get_settings
from app.prompts import CHAT_INSTRUCTIONS
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(
    title="AI Chatbot API",
    description=(
        "Openai-powered backend for the HTML/CSS/JavaScript and Docker compose lab"
        ),
    version="1.0.0",
    root_path="/api"
)

def get_openai_client(settings: Settings = Depends(get_settings)) -> OpenAI | None:
    """Create a server-side OpenAI client without exposing the API key."""

    if not settings.has_openai_api_key:
        return None
    
    return OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=45.0,
        max_retries=2
    )


@app.get("/", tags=["service"])
def root(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "message": "FastAPI chatbot backend is running.",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "checked_at": datetime.now(UTC).isoformat(),
    }


@app.get("/info", tags=["service"])
def info(settings: Settings = Depends(get_settings)) -> dict[str, str | bool]:
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "app_version": settings.app_version,
        "model": settings.openai_model,
        "openai_configured": settings.has_openai_api_key,
    }


@app.post(
        "/chat",
        response_model=ChatResponse,
        tags=["chat"]
)
def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    client: OpenAI | None = Depends(get_openai_client),
) -> ChatResponse:
    """Generate one assistant reply from the bounded conversation history."""

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OPENAI_API_KEY가 설정되지 않았습니다. "
                "서버의 api.env 파일을 확인하세요."
            ),
        )

    input_messages = [
        {"role": message.role, "content": message.content}
        for message in request.messages
    ]

    try:
        response = client.responses.create(
            model=settings.openai_model,
            reasoning={'effort':"low"}, # 모델의 추론 수준 낮게 설정. 빠른 응답과 비용 절감에 유리
            instructions=CHAT_INSTRUCTIONS,
            input=input_messages,
            max_output_tokens=settings.max_output_tokens,
            store=False     # OpenAI 측에 응답 객체를 저장하지 않도록 요청
        )
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
        ) from exc
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI API에 연결하지 못했습니다.",
        ) from exc
    except APIStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API가 오류를 반환했습니다. 상태 코드: {exc.status_code}",
        ) from exc

    reply = response.output_text.strip()
    if not reply:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="모델이 텍스트 응답을 반환하지 않았습니다.",
        )

    return ChatResponse(
        reply=reply,
        model=response.model or settings.openai_model,
        response_id=response.id,
    )