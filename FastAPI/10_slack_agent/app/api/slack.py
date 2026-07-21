from __future__ import annotations





@router.post("")
async def slack_events(request: Request):
    handler = 
    if handler is None:
        raise HTTPException(
            status_code=,
            detail="Slack 연동이 설정되지 않았습니다.",
        )
    return await

