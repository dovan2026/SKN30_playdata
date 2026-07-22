from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(tags=["slack"])


# Slack Events API와 슬래시('/') 명령 요청을 받는 단일 엔드포인트
@router.post("/slack/events")
async def slack_events(request: Request):
    handler = getattr(request.app.state, "slack_request_handler", None)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack 연동이 설정되지 않았습니다.",
        )
    # 이벤트 분류 등 실제 처리는 Slack Bolt 핸들러에 위임한다.
    return await handler.handle(request)
