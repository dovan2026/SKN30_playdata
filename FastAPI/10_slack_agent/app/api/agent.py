from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.agent import AgentRequest, AgentResponse, ErrorResponse

# 이 파일의 모든 주소 앞에 /agent를 붙이고 Swagger 문서에서 agent로 묶는다.
router = APIRouter(prefix="/agent", tags=['agent'])


# Post /agent/run 엔드포인트의 응답 스키마와 예상 오류를 API 문서에 등록
@router.post(
    "/run",
    response_model=AgentResponse,
    responses={
        502: {"model": ErrorResponse, "description": "Search or analysis failed"},
        503: {"description": "Agent is not configured"},
    },
)
async def run_agent(request: Request, payload: AgentRequest) -> AgentResponse:
    # Fastapi 앱에 저장된 agent_service를 안전하게 가져오는 코드
    # agent_service가 없다면 AttrivuteError 발생을 하는데 이때 오류 대신 None 받을 수 있음
    service = getattr(request.app.state, "agent_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE ,
            detail="OPENAI_API_KEY와 TAVILY_API_KEY 설정이 필요합니다.",
        )
    # 검증된 요청 데이터를 서비스 계층에 전달하고 분석이 끝날때 까지 기다림.
    return await service.run(query=payload.query, thread_id=payload.thread_id)from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.agent import AgentRequest, AgentResponse, ErrorResponse

# 이 파일의 모든 주소 앞에 /agent를 붙이고 Swagger 문서에서 agent로 묶는다.

# Post /agent/run 엔드포인트의 응답 스키마와 예상 오류를 API 문서에 등록
@router.post(
    '/run',
    response_model=AgentResponse,
    responses={
        502: {"model": ErrorResponse, "description": "Search or analysis failed"},
        503: {"description": "Agent is not configured"},
    },
)
async def run_agent(request: Request, payload: AgentRequest) -> AgentResponse:
    # FastAPI 앱에 저장된 agent_service를 안전하게 가져오는 코드
    # agent_service가 없다면 AttributeError 발생을 하는데 이때 오류 대신 None 받을 수 있음
    service = getattr(request.app.state, 'agent_service', None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY와 TAVILY_API_KEY 설정이 필요합니다.",
        )
    # 검증된 요청 데이터를 서비스 계층에 전달하고 분석이 끝날때까지 기다림
    return await service.run(query=payload.query, thread_id=payload.thread_id)

@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    missing = settings.missing_agent_settings()

    worker_ready = bool(getattr(request.app.state, "worker_ready", False))

    ready_now = not missing and worker_ready

    return JSONResponse(
        status_code=status.HTTP_200_OK if ready_now else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if ready_now else "not_ready",
            "missing_settings": missing,
            "worker_ready": worker_ready,
        },
    )
