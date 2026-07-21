"""프로젝트 글ego 4대 파이프라인 통합 고도화 전용 작업 프롬프트 빌더."""

from __future__ import annotations
from tools import PROJECT_NAMES, ProjectType


# 1. 글ego 출판 파이프라인
def build_ego_nudge_task(
    author_id: str,
    stagnation_days: int,
    total_chars: int,
    last_week_delta: int,
    cohort_id: str,
    project_type: ProjectType,
    current_week: int,
) -> str:
    proj_name = PROJECT_NAMES.get(project_type, "글ego 출판 프로젝트")
    return f"""
글ego 작가 케어 정보:
- 작가 ID/성함: {author_id}
- 소속 기수: {cohort_id} ({proj_name})
- 현재 진행 상황: {current_week}주차 진행 중
- 집필 정체 일수: {stagnation_days}일째 원고 업로드 정체
- 누적 총 글자수: {total_chars:,}자
- 지난 주 작성 분량: {last_week_delta:,}자

위 작가님의 상황에 맞추어 그로스 매니저가 전달할 다정하고 동기부여가 되는 1:1 케어 메시지 초안을 작성하세요.
""".strip()


def build_ego_qa_task(
    author_id: str,
    question: str,
    keyword_hint: str,
    cohort_id: str,
    project_type: ProjectType,
    qa_history: list[dict] | None = None,
) -> str:
    proj_name = PROJECT_NAMES.get(project_type, "글ego 출판 프로젝트")
    history_text = ""
    if qa_history:
        recent = qa_history[-3:]
        history_lines = "\n".join(
            f"- [{item.get('label', '?')}] Q: {item.get('question', '')} → A: {item.get('approved_answer', '(미승인)')}"
            for item in recent
        )
        history_text = f"\n이전 작가 문의 이력:\n{history_lines}\n"

    return f"""
글ego 작가 문의 정보:
- 작가 ID/성함: {author_id}
- 소속 기수: {cohort_id} ({proj_name})

작가의 문의/요청 내용:
"{question}"

키워드 1차 분류 힌트: {keyword_hint}
{history_text}
위 질문의 유형을 정확히 분류하고 매니저가 발송할 답변 초안을 작성해 주세요.
""".strip()


# 2. 모두출판 SaaS 크로스셀링 (A/B 테스트 카피)
def build_ab_sales_copy_task(text_excerpt: str, error_score: int, issues: list[str]) -> str:
    issues_str = "\n".join(f"- {issue}" for issue in issues) if issues else "- 교열 및 띄어쓰기 교정 필요"
    return f"""
유저 원고 정보:
- 원고 발췌: "{text_excerpt[:200]}..."
- 에러 위험도: {error_score}점 (HIGH RISK)
- 주요 교정 이슈:
{issues_str}

위 유저를 '교정의 신' 유료 교정 서비스로 즉시 전환시키기 위한 [버전 A: 손실 회피형] 카피와 [버전 B: 성과 강조형] 카피를 각각 작성하세요.
""".strip()


# 3. 모두의 자서전 인터뷰어 파이프라인
def build_interviewer_task(chat_history: list[dict], current_chapter_title: str) -> str:
    history_str = "\n".join(f"[{msg['role']}]: {msg['content']}" for msg in chat_history[-6:])
    return f"""
현재 진행 챕터: {current_chapter_title}

최근 대화 기록:
{history_str}

위 유저의 답변에 다정하게 공감하고, 해당 챕터 주제에 맞는 세부적인 감정과 에피소드를 끌어내는 꼬리 질문 1개를 던지세요.
""".strip()


def build_timeline_extraction_task(chat_history: list[dict]) -> str:
    history_str = "\n".join(f"[{msg['role']}]: {msg['content']}" for msg in chat_history)
    return f"""
전체 인터뷰 대화 기록:
{history_str}

위 대화에서 유저의 인생 타임라인 맵(시기, 장소, 핵심 인물, 사건, 감정)을 추출 정리해 주세요.
""".strip()


def build_essay_compiler_task(extracted_facts: str, chat_history: list[dict], chapter_title: str) -> str:
    return f"""
자서전 챕터 제목: {chapter_title}
추출된 핵심 사실:
{extracted_facts}

위 내용을 바탕으로 감동적이고 문학성이 풍부한 1인칭 수필 형태의 자서전 챕터 원고를 작성하세요.
""".strip()


def build_essay_refinement_task(current_chapter: str, user_feedback: str) -> str:
    return f"""
기존 자서전 챕터 원고:
--- 원고 시작 ---
{current_chapter}
--- 원고 끝 ---

유저의 수정 요청 피드백:
"{user_feedback}"

유저의 피드백을 정확하게 반영하여 다듬어진 최종 자서전 챕터 원고를 새로 출력하세요.
""".strip()


# 4. 다윈의 서재 작가 소싱 파이프라인 (출판 기획서 & 5대 추천 목차)
def build_pitching_proposal_task(author_name: str, keyword: str, past_summary: str, match_score: float) -> str:
    return f"""
소싱 후보 작가 정보:
- 작가 성함: {author_name}
- 과거 원고/전문성: {past_summary}
- 매칭 트렌드 키워드: "{keyword}"
- 하이브리드 매칭 점수: {match_score}%

'다윈의 서재' 이름으로 작가님께 보낼 [1. 출판 제안 이메일 초안]과 [2. 5대 추천 목차 기획서]를 완벽하게 구성해 주세요.
""".strip()
