"""
프로젝트 글ego 4대 파이프라인 자율 관리를 위한 LangGraph 그래프 정의 (고도화 버전).

그래프 구조:
  1. monitoring_graph & qa_graph: 출판 원고 모니터링 & 작가 1:1 케어 그래프 (Human-in-the-Loop Interrupt)
  2. biography_graph           : 모두의 자서전 4대 챕터 목차 트리 + 인생 타임라인 맵 + 원고 공동수정 루프 그래프
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, NotRequired, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents import (
    ESSAY_COMPILER_SYSTEM_PROMPT,
    ESSAY_REFINEMENT_SYSTEM_PROMPT,
    INTERVIEWER_SYSTEM_PROMPT,
    NUDGE_SYSTEM_PROMPT,
    QA_CLASSIFIER_SYSTEM_PROMPT,
    TIMELINE_EXTRACTOR_SYSTEM_PROMPT,
    run_agent,
)
from tasks import (
    build_ego_nudge_task,
    build_ego_qa_task,
    build_essay_compiler_task,
    build_essay_refinement_task,
    build_interviewer_task,
    build_timeline_extraction_task,
)
from tools import (
    ProjectType,
    analyze_ego_authors,
    build_ego_dashboard_summary,
    calculate_ego_milestones,
    classify_ego_question,
    compute_delta,
    get_critical_authors,
    get_current_biography_chapter,
    get_current_week,
)


class EgoPublishState(TypedDict):
    cohort_id: str
    project_type: ProjectType
    cohort_start_date: str

    milestones: NotRequired[dict]
    author_manuscripts: NotRequired[dict[str, list[int]]]

    stagnation_days: NotRequired[dict[str, int]]
    stagnation_labels: NotRequired[dict[str, str]]

    current_qa: NotRequired[dict]
    qa_log: NotRequired[list[dict]]

    nudge_draft: NotRequired[str]
    nudge_target_author: NotRequired[str]
    qa_draft: NotRequired[dict]

    approval_status: NotRequired[str]
    approved_message: NotRequired[str]

    dispatched_messages: NotRequired[list[dict]]
    dashboard_summary: NotRequired[dict]


class BiographyState(TypedDict):
    session_id: str
    chat_history: list[dict]
    current_chapter_info: NotRequired[dict] # {chapter_num, title, target_turns}
    extracted_facts: NotRequired[str]
    timeline_map: NotRequired[str]           # 인생 타임라인 맵
    draft_chapter: NotRequired[str]
    user_feedback: NotRequired[str]          # 원고 공동수정 요청 피드백
    turn_count: NotRequired[int]
    status: NotRequired[str]                 # "interviewing" | "compiled" | "refined"


AgentRunner = Callable[[str, str], str]


def create_ego_publish_graph(agent_runner: AgentRunner = run_agent):
    def onboarding_node(state: EgoPublishState) -> dict:
        milestone_data = calculate_ego_milestones(
            cohort_id=state["cohort_id"],
            project_type=state.get("project_type", "joint_publishing"),
            start_date_str=state["cohort_start_date"],
        )
        return {
            "milestones": milestone_data,
            "author_manuscripts": state.get("author_manuscripts", {}),
            "stagnation_days": {},
            "stagnation_labels": {},
            "qa_log": state.get("qa_log", []),
            "dispatched_messages": state.get("dispatched_messages", []),
            "approval_status": "pending",
        }

    def monitoring_node(state: EgoPublishState) -> dict:
        author_manuscripts = state.get("author_manuscripts", {})
        project_type = state.get("project_type", "joint_publishing")

        if not author_manuscripts:
            return {
                "stagnation_labels": {},
                "stagnation_days": {},
                "dashboard_summary": {"authors": [], "summary": {}},
            }

        stagnation_labels, stagnation_days = analyze_ego_authors(
            author_manuscripts, project_type=project_type
        )

        dashboard_summary = build_ego_dashboard_summary(
            author_manuscripts=author_manuscripts,
            stagnation_labels=stagnation_labels,
            stagnation_days=stagnation_days,
            project_type=project_type,
        )

        return {
            "stagnation_labels": stagnation_labels,
            "stagnation_days": stagnation_days,
            "dashboard_summary": dashboard_summary,
        }

    def nudge_node(state: EgoPublishState) -> dict:
        stagnation_labels = state.get("stagnation_labels", {})
        stagnation_days = state.get("stagnation_days", {})
        author_manuscripts = state.get("author_manuscripts", {})
        project_type = state.get("project_type", "joint_publishing")

        critical_authors = get_critical_authors(stagnation_labels)
        if not critical_authors:
            return {"nudge_draft": "", "nudge_target_author": "", "approval_status": "pending"}

        target_author = critical_authors[0]
        char_log = author_manuscripts.get(target_author, [])
        deltas = compute_delta(char_log)

        nudge_draft = agent_runner(
            NUDGE_SYSTEM_PROMPT,
            build_ego_nudge_task(
                author_id=target_author,
                stagnation_days=stagnation_days.get(target_author, 0),
                total_chars=char_log[-1] if char_log else 0,
                last_week_delta=deltas[-1] if deltas else 0,
                cohort_id=state.get("cohort_id", ""),
                project_type=project_type,
                current_week=get_current_week(state.get("cohort_start_date", "2025-01-01")),
            ),
        )

        return {
            "nudge_draft": nudge_draft,
            "nudge_target_author": target_author,
            "approval_status": "pending",
        }

    def qa_node(state: EgoPublishState) -> dict:
        current_qa = state.get("current_qa", {})
        if not current_qa:
            return {"qa_draft": {}, "approval_status": "pending"}

        author_id = current_qa.get("author_id", "unknown")
        question = current_qa.get("question", "")
        project_type = state.get("project_type", "joint_publishing")
        keyword_hint = classify_ego_question(question)

        qa_response = agent_runner(
            QA_CLASSIFIER_SYSTEM_PROMPT,
            build_ego_qa_task(
                author_id=author_id,
                question=question,
                keyword_hint=keyword_hint,
                cohort_id=state.get("cohort_id", ""),
                project_type=project_type,
                qa_history=state.get("qa_log", []),
            ),
        )

        lines = qa_response.strip().split("\n")
        label = keyword_hint
        draft_answer_lines = []
        in_answer_section = False

        for line in lines:
            if "질문 유형" in line:
                continue
            if line.startswith("[") and "]" in line:
                inner = line.strip("[]").replace("분류 결과:", "").strip()
                label = inner.split()[0] if inner else keyword_hint
            elif "답변 초안" in line:
                in_answer_section = True
            elif in_answer_section:
                draft_answer_lines.append(line)

        draft_answer = "\n".join(draft_answer_lines).strip() or qa_response

        return {
            "qa_draft": {
                "author_id": author_id,
                "question": question,
                "label": label,
                "draft_answer": draft_answer,
                "raw_response": qa_response,
            },
            "approval_status": "pending",
        }

    def dispatch_node(state: EgoPublishState) -> dict:
        dispatched = list(state.get("dispatched_messages", []))
        approved_message = state.get("approved_message", "")
        approval_status = state.get("approval_status", "pending")

        if approval_status == "approved" and approved_message:
            import datetime

            qa_draft = state.get("qa_draft", {})
            nudge_target = state.get("nudge_target_author", "")

            if qa_draft and qa_draft.get("author_id"):
                msg_type = "qa_answer"
                target = qa_draft["author_id"]
            elif nudge_target:
                msg_type = "nudge"
                target = nudge_target
            else:
                msg_type = "general"
                target = "unknown"

            dispatched.append({
                "type": msg_type,
                "target_author": target,
                "message": approved_message,
                "dispatched_at": datetime.datetime.now().isoformat(),
                "status": "sent",
            })

            qa_log = list(state.get("qa_log", []))
            if qa_draft and qa_draft.get("author_id"):
                qa_copy = dict(qa_draft)
                qa_copy["approved_answer"] = approved_message
                qa_copy["approved_at"] = datetime.datetime.now().isoformat()
                qa_log.append(qa_copy)

            return {
                "dispatched_messages": dispatched,
                "qa_log": qa_log,
                "approval_status": "dispatched",
            }

        return {
            "approval_status": approval_status,
            "dispatched_messages": dispatched,
        }

    def wait_node(state: EgoPublishState) -> dict:
        return {"approval_status": "waiting"}

    def route_by_stagnation(state: EgoPublishState) -> Literal["nudge_node", "wait_node"]:
        stagnation_labels = state.get("stagnation_labels", {})
        critical_authors = get_critical_authors(stagnation_labels)
        if critical_authors:
            return "nudge_node"
        return "wait_node"

    monitoring_builder = StateGraph(EgoPublishState)
    monitoring_builder.add_node("onboarding_node", onboarding_node)
    monitoring_builder.add_node("monitoring_node", monitoring_node)
    monitoring_builder.add_node("nudge_node", nudge_node)
    monitoring_builder.add_node("dispatch_node", dispatch_node)
    monitoring_builder.add_node("wait_node", wait_node)

    monitoring_builder.add_edge(START, "onboarding_node")
    monitoring_builder.add_edge("onboarding_node", "monitoring_node")
    monitoring_builder.add_conditional_edges(
        "monitoring_node",
        route_by_stagnation,
        {
            "nudge_node": "nudge_node",
            "wait_node": "wait_node",
        },
    )
    monitoring_builder.add_edge("nudge_node", "dispatch_node")
    monitoring_builder.add_edge("wait_node", END)
    monitoring_builder.add_edge("dispatch_node", END)

    qa_builder = StateGraph(EgoPublishState)
    qa_builder.add_node("qa_node", qa_node)
    qa_builder.add_node("dispatch_node", dispatch_node)
    qa_builder.add_edge(START, "qa_node")
    qa_builder.add_edge("qa_node", "dispatch_node")
    qa_builder.add_edge("dispatch_node", END)

    checkpointer = MemorySaver()

    monitoring_graph = monitoring_builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["dispatch_node"],
    )
    qa_graph = qa_builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["dispatch_node"],
    )

    return monitoring_graph, qa_graph, checkpointer


# ────────────────────────────────────────────────────────────────────────────
# 4. 모두의 자서전 다이내믹 인터뷰어 그래프 (고도화 버전)
# ────────────────────────────────────────────────────────────────────────────

def create_biography_graph(agent_runner: AgentRunner = run_agent):
    """
    [고도화] 4대 챕터 목차 트리 + 인생 타임라인 맵 추출 + 유저 원고 공동수정 루프가 탑재된
    모두의 자서전 StateGraph.
    """

    def interview_node(state: BiographyState) -> dict:
        chat_history = state.get("chat_history", [])
        user_turns = sum(1 for m in chat_history if m.get("role") == "user")

        chapter_info = get_current_biography_chapter(user_turns)

        next_question = agent_runner(
            INTERVIEWER_SYSTEM_PROMPT,
            build_interviewer_task(chat_history, chapter_info["title"]),
        )

        updated_history = list(chat_history)
        updated_history.append({"role": "assistant", "content": next_question})

        return {
            "chat_history": updated_history,
            "current_chapter_info": chapter_info,
            "turn_count": user_turns,
            "status": "interviewing",
        }

    def timeline_node(state: BiographyState) -> dict:
        chat_history = state.get("chat_history", [])
        timeline_map = agent_runner(
            TIMELINE_EXTRACTOR_SYSTEM_PROMPT,
            build_timeline_extraction_task(chat_history),
        )
        return {"timeline_map": timeline_map}

    def compile_node(state: BiographyState) -> dict:
        chat_history = state.get("chat_history", [])
        timeline_map = state.get("timeline_map", "")
        chapter_info = state.get("current_chapter_info", {"title": "1장. 나의 삶과 기억"})

        draft_chapter = agent_runner(
            ESSAY_COMPILER_SYSTEM_PROMPT,
            build_essay_compiler_task(timeline_map, chat_history, chapter_info["title"]),
        )

        return {
            "draft_chapter": draft_chapter,
            "status": "compiled",
        }

    def refinement_node(state: BiographyState) -> dict:
        current_chapter = state.get("draft_chapter", "")
        user_feedback = state.get("user_feedback", "")

        if not user_feedback:
            return {"status": "compiled"}

        refined_chapter = agent_runner(
            ESSAY_REFINEMENT_SYSTEM_PROMPT,
            build_essay_refinement_task(current_chapter, user_feedback),
        )

        return {
            "draft_chapter": refined_chapter,
            "status": "refined",
        }

    def route_after_interview(state: BiographyState) -> Literal["timeline_node", "refinement_node", "end"]:
        user_feedback = state.get("user_feedback", "")
        if user_feedback:
            return "refinement_node"

        chat_history = state.get("chat_history", [])
        user_turns = sum(1 for m in chat_history if m.get("role") == "user")
        if user_turns >= 3:
            return "timeline_node"
        return "end"

    bio_builder = StateGraph(BiographyState)
    bio_builder.add_node("interview_node", interview_node)
    bio_builder.add_node("timeline_node", timeline_node)
    bio_builder.add_node("compile_node", compile_node)
    bio_builder.add_node("refinement_node", refinement_node)

    bio_builder.add_edge(START, "interview_node")
    bio_builder.add_conditional_edges(
        "interview_node",
        route_after_interview,
        {
            "timeline_node": "timeline_node",
            "refinement_node": "refinement_node",
            "end": END,
        },
    )
    bio_builder.add_edge("timeline_node", "compile_node")
    bio_builder.add_edge("compile_node", END)
    bio_builder.add_edge("refinement_node", END)

    bio_checkpointer = MemorySaver()
    biography_graph = bio_builder.compile(checkpointer=bio_checkpointer)

    return biography_graph, bio_checkpointer


monitoring_graph, qa_graph, graph_checkpointer = create_ego_publish_graph()
biography_graph, bio_checkpointer = create_biography_graph()
