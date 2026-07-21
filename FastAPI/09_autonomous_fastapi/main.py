"""
프로젝트 글ego 4대 파이프라인 통합 고도화 그로스 매니저 OS — FastAPI 애플리케이션.

고도화 API 라인업:
  1. 📖 글ego 출판 파이프라인    : 슬럼프 지수(Burnout Index), 12주 원고 모니터링 & 1:1 케어
  2. ⚡ 모두출판 SaaS 크로스셀링 : 1:1 교정 Before/After 비교, A/B 세일즈 카피(손실회피/성과강조), 다이내믹 쿠폰
  3. 🎙️ 모두의 자서전 인터뷰어 : 4대 챕터 목차 트리, 인생 타임라인 맵 추출, 원고 공동수정(Refinement) 루프
  4. 🔍 다윈의 서재 작가 소싱   : 하이브리드 검색 (Vector Embedding + BM25 융합), 5대 추천 목차 동반 기획서
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agents import (
    PITCHING_PROPOSAL_SYSTEM_PROMPT,
    SALES_COPY_AB_TEST_PROMPT,
    run_agent,
)
from graph import biography_graph, monitoring_graph, qa_graph
from tasks import build_ab_sales_copy_task, build_pitching_proposal_task
from tools import (
    ProjectType,
    analyze_manuscript_error_score,
    calculate_dynamic_pricing_tier,
    fetch_trending_keywords,
    generate_before_after_diff,
    hybrid_search_authors,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="프로젝트 글ego 4대 파이프라인 통합 고도화 그로스 OS",
    version="4.0.0",
    description=(
        "프로젝트 글ego (Ego Writing) 4대 비즈니스 파이프라인 심층 고도화 에이전트 시스템입니다.\n\n"
        "1. **📖 글ego 출판 파이프라인**: 다차원 작가 슬럼프 지수(Burnout Index) & 1:1 케어\n"
        "2. **⚡ 모두출판 SaaS 크로스셀링**: 1:1 교정 Before/After 비교 & A/B 테스트 세일즈 카피\n"
        "3. **🎙️ 모두의 자서전 인터뷰어**: 4대 챕터 트리 & 인생 타임라인 맵 & 원고 공동수정 루프\n"
        "4. **🔍 다윈의 서재 작가 소싱**: 하이브리드 벡터+BM25 검색 & 5대 추천 목차 동반 기획서"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic 스키마
class CohortOnboardInput(BaseModel):
    cohort_id: str = Field(..., example="Ego-Joint-42기")
    project_type: ProjectType = Field(default="joint_publishing")
    cohort_start_date: str = Field(..., example="2025-01-06")
    author_manuscripts: dict[str, list[int]] = Field(
        default_factory=dict,
        example={
            "작가_김에고": [0, 2100, 4200, 6500],
            "작가_이책": [0, 1900, 3900, 4000],
            "작가_박원고": [0, 500, 600, 650],
        },
    )

class MonitoringRunInput(BaseModel):
    thread_id: str
    author_manuscripts: dict[str, list[int]]

class ApprovalInput(BaseModel):
    thread_id: str
    approved_message: str
    action: str = Field(default="approved")

class QASubmitInput(BaseModel):
    cohort_id: str = Field(..., example="Ego-Joint-42기")
    project_type: ProjectType = Field(default="joint_publishing")
    cohort_start_date: str = Field(default="2025-01-06")
    author_id: str = Field(..., example="작가_김에고")
    question: str

class CrossSellAnalyzeInput(BaseModel):
    user_id: str = Field(default="user_modu_01")
    manuscript_text: str = Field(
        ...,
        example="나는 작년 3월에 퇴사했었었다. 그때 내 기분은 너무나도 슬펐었다. 하지만 글을 쓰기 시작했에 있어서 새로운 희망을 발견하게 되었었다...",
    )

class BiographyChatInput(BaseModel):
    session_id: str = Field(..., example="bio_session_1001")
    user_message: str = Field(..., example="마당에 커다란 감나무가 있던 시골집에서 어린 시절을 보냈어요.")
    current_topic: str = Field(default="1장. 유년기와 고향의 기억")
    user_feedback: str | None = Field(default=None, description="원고 공동수정 요청 피드백 (선택)")


@app.get("/", tags=["Root"])
async def root():
    return {
        "system": "프로젝트 글ego 4대 파이프라인 통합 고도화 그로스 OS",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "version": "4.0.0",
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard():
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="대시보드 파일이 없습니다.")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── 1. 글ego 출판 파이프라인 ───────────────────────────────────────────────

@app.post("/cohort/onboard", tags=["1. 글ego 출판 파이프라인"])
async def cohort_onboard(input_data: CohortOnboardInput):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "cohort_id": input_data.cohort_id,
        "project_type": input_data.project_type,
        "cohort_start_date": input_data.cohort_start_date,
        "author_manuscripts": input_data.author_manuscripts,
        "qa_log": [],
        "dispatched_messages": [],
    }

    try:
        await asyncio.to_thread(monitoring_graph.invoke, initial_state, config)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = monitoring_graph.get_state(config)
    current_state: dict = snapshot.values if snapshot.values else {}

    return {
        "thread_id": thread_id,
        "cohort_id": input_data.cohort_id,
        "project_type": input_data.project_type,
        "milestones": current_state.get("milestones", {}),
        "dashboard_summary": current_state.get("dashboard_summary", {}),
        "message": (
            f"글ego '{input_data.cohort_id}' 온보딩 완료. "
            + (
                "⚠️ 집필 정체 작가가 발견되어 넛지 메시지가 생성되었습니다."
                if current_state.get("nudge_draft")
                else "✅ 모든 작가님이 순항 집필 중입니다."
            )
        ),
    }


@app.post("/monitoring/run", tags=["1. 글ego 출판 파이프라인"])
async def monitoring_run(input_data: MonitoringRunInput):
    config = {"configurable": {"thread_id": input_data.thread_id}}
    snapshot = monitoring_graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        await asyncio.to_thread(
            monitoring_graph.invoke,
            {"author_manuscripts": input_data.author_manuscripts},
            config,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = monitoring_graph.get_state(config)
    current_state: dict = snapshot.values if snapshot.values else {}

    return {
        "thread_id": input_data.thread_id,
        "stagnation_labels": current_state.get("stagnation_labels", {}),
        "stagnation_days": current_state.get("stagnation_days", {}),
        "dashboard_summary": current_state.get("dashboard_summary", {}),
        "nudge_draft": current_state.get("nudge_draft", ""),
        "nudge_target_author": current_state.get("nudge_target_author", ""),
        "approval_status": current_state.get("approval_status", ""),
    }


@app.get("/monitoring/state", tags=["1. 글ego 출판 파이프라인"])
async def monitoring_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = monitoring_graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    state: dict = snapshot.values
    return {
        "thread_id": thread_id,
        "stagnation_labels": state.get("stagnation_labels", {}),
        "stagnation_days": state.get("stagnation_days", {}),
        "dashboard_summary": state.get("dashboard_summary", {}),
        "nudge_draft": state.get("nudge_draft", ""),
        "nudge_target_author": state.get("nudge_target_author", ""),
        "approval_status": state.get("approval_status", ""),
        "dispatched_messages": state.get("dispatched_messages", []),
    }


@app.post("/monitoring/approve", tags=["1. 글ego 출판 파이프라인"])
async def monitoring_approve(input_data: ApprovalInput):
    config = {"configurable": {"thread_id": input_data.thread_id}}
    snapshot = monitoring_graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    approval_update = {
        "approval_status": input_data.action,
        "approved_message": input_data.approved_message if input_data.action == "approved" else "",
    }
    try:
        await asyncio.to_thread(monitoring_graph.invoke, approval_update, config)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = monitoring_graph.get_state(config)
    final_state: dict = snapshot.values if snapshot.values else {}
    return {
        "thread_id": input_data.thread_id,
        "action": input_data.action,
        "dispatched_messages": final_state.get("dispatched_messages", []),
        "message": "✅ 넛지 메시지가 작가님께 발송되었습니다." if input_data.action == "approved" else "❌ 거절되었습니다.",
    }


@app.post("/qa/submit", tags=["1. 글ego 출판 파이프라인"])
async def qa_submit(input_data: QASubmitInput):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "cohort_id": input_data.cohort_id,
        "project_type": input_data.project_type,
        "cohort_start_date": input_data.cohort_start_date,
        "current_qa": {"author_id": input_data.author_id, "question": input_data.question},
        "qa_log": [],
        "dispatched_messages": [],
        "approval_status": "pending",
    }
    try:
        await asyncio.to_thread(qa_graph.invoke, initial_state, config)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = qa_graph.get_state(config)
    state: dict = snapshot.values if snapshot.values else {}
    return {
        "thread_id": thread_id,
        "author_id": input_data.author_id,
        "question": input_data.question,
        "qa_draft": state.get("qa_draft", {}),
        "approval_status": state.get("approval_status", ""),
        "message": "🤖 AI 답변 초안이 작성되었습니다.",
    }


@app.post("/qa/approve", tags=["1. 글ego 출판 파이프라인"])
async def qa_approve(input_data: ApprovalInput):
    config = {"configurable": {"thread_id": input_data.thread_id}}
    snapshot = qa_graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    approval_update = {
        "approval_status": input_data.action,
        "approved_message": input_data.approved_message if input_data.action == "approved" else "",
    }
    try:
        await asyncio.to_thread(qa_graph.invoke, approval_update, config)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = qa_graph.get_state(config)
    final_state: dict = snapshot.values if snapshot.values else {}
    return {
        "thread_id": input_data.thread_id,
        "action": input_data.action,
        "dispatched_messages": final_state.get("dispatched_messages", []),
        "message": "✅ QA 답변이 발송되었습니다.",
    }


# ── 2. 모두출판 SaaS 크로스셀링 파이프라인 (고도화) ─────────────────────────

@app.post("/cross-sell/analyze", tags=["2. 모두출판 SaaS 크로스셀링"])
async def cross_sell_analyze(input_data: CrossSellAnalyzeInput):
    """
    [고도화] 원고 에러 분석 + 1:1 교정 Before/After 비교 프리뷰 + 다이내믹 쿠폰 + A/B 세일즈 카피 동시 생성
    """
    text = input_data.manuscript_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="원고 텍스트를 입력해주세요.")

    analysis = analyze_manuscript_error_score(text)
    diff_preview = generate_before_after_diff(text)
    pricing_tier = calculate_dynamic_pricing_tier(analysis["error_score"], analysis["char_count"])

    ab_copy_response = run_agent(
        SALES_COPY_AB_TEST_PROMPT,
        build_ab_sales_copy_task(text, analysis["error_score"], analysis["issues"]),
    )

    return {
        "user_id": input_data.user_id,
        "analysis": analysis,
        "diff_preview": diff_preview,
        "pricing_tier": pricing_tier,
        "ab_sales_copies": ab_copy_response,
        "upsell_prompt_triggered": analysis["error_score"] >= 70,
    }


# ── 3. 모두의 자서전 다이내믹 인터뷰어 파이프라인 (고도화) ─────────────────────

@app.post("/biography/chat", tags=["3. 모두의 자서전 인터뷰어"])
async def biography_chat(input_data: BiographyChatInput):
    """
    [고도화] 4대 챕터 목차 트리 + 인생 타임라인 맵 추출 + 유저 원고 공동수정(Refinement) 지원
    """
    config = {"configurable": {"thread_id": input_data.session_id}}
    snapshot = biography_graph.get_state(config)

    existing_state: dict = snapshot.values if snapshot.values else {
        "session_id": input_data.session_id,
        "chat_history": [],
        "current_topic": input_data.current_topic,
        "turn_count": 0,
    }

    update_payload = {
        "session_id": input_data.session_id,
        "current_topic": input_data.current_topic,
    }

    if input_data.user_feedback:
        update_payload["user_feedback"] = input_data.user_feedback
    else:
        chat_history = list(existing_state.get("chat_history", []))
        chat_history.append({"role": "user", "content": input_data.user_message})
        update_payload["chat_history"] = chat_history

    try:
        await asyncio.to_thread(biography_graph.invoke, update_payload, config)
    except Exception as error:
        logger.exception("자서전 인터뷰어 실행 에러")
        raise HTTPException(status_code=500, detail=str(error)) from error

    snapshot = biography_graph.get_state(config)
    final_state: dict = snapshot.values if snapshot.values else {}
    history = final_state.get("chat_history", [])
    latest_reply = history[-1]["content"] if history and history[-1]["role"] == "assistant" else "답변해 주셔서 감사합니다."

    return {
        "session_id": input_data.session_id,
        "turn_count": final_state.get("turn_count", 1),
        "current_chapter_info": final_state.get("current_chapter_info", {}),
        "latest_assistant_reply": latest_reply,
        "timeline_map": final_state.get("timeline_map", ""),
        "draft_chapter": final_state.get("draft_chapter", ""),
        "is_compiled": bool(final_state.get("draft_chapter")),
        "status": final_state.get("status", "interviewing"),
    }


# ── 4. 다윈의 서재 작가 소싱 파이프라인 (고도화) ─────────────────────────────

@app.get("/sourcing/run", tags=["4. 다윈의 서재 작가 소싱"])
async def sourcing_run(keyword: str | None = None):
    """
    [고도화] 트렌드 지수 수집 → 하이브리드(Vector+BM25) 매칭 → 출판 제안서 & 5대 추천 목차 기획서 자동 생성
    """
    trending_list = fetch_trending_keywords()
    target_keyword = keyword if keyword else trending_list[0]["keyword"]

    matches = hybrid_search_authors(target_keyword, top_k=2)
    top_author = matches[0] if matches else None

    proposal_response = ""
    if top_author:
        proposal_response = run_agent(
            PITCHING_PROPOSAL_SYSTEM_PROMPT,
            build_pitching_proposal_task(
                author_name=top_author["author_name"],
                keyword=target_keyword,
                past_summary=top_author["past_work_summary"],
                match_score=top_author["match_score"],
            ),
        )

    return {
        "target_keyword": target_keyword,
        "trending_keywords": trending_list,
        "top_matches": matches,
        "selected_author": top_author,
        "proposal_and_email": proposal_response,
        "search_type": "Hybrid (OpenAI text-embedding-3-small + BM25)",
        "status": "ready_for_pitching",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
