from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

# health
# 상태 확인 주소를 /health 아래에 묶는다.
router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


# ready
# 실제 요청을 처리할 준비가 되었는지 확인
@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    # 에이전트 실행에 필요한 환경변수 확인
    settings = request.app.state.settings
    missing = settings.missing_agent_settings()

    #AgentService가 생성되어 작업을 받을 수 있는 상태인지 확인 
    worker_ready = bool(getattr(request.app.state, "worker_ready", False))

    # 필수 설정이 모두 되어 있고, 작업자도 준비된 경우 ready
    ready_now = not missing and worker_ready

    return JSONResponse(
        status_code=status.HTTP_200_OK if ready_now else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if ready_now else "not_ready",
            "missing_settings": missing,
            "worker_ready": worker_ready,
        },
    )