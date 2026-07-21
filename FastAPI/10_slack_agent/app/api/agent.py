from __future__ import annotations




@router.post(
    ,
    response_model=,
    responses={
        502: {"model": ErrorResponse, "description": "Search or analysis failed"},
        503: {"description": "Agent is not configured"},
    },
)
async def run_agent(request: Request, payload: AgentRequest) -> AgentResponse:
    service = 
    if service is None:
        raise HTTPException(
            status_code= ,
            detail="OPENAI_API_KEY와 TAVILY_API_KEY 설정이 필요합니다.",
        )
    return await 
