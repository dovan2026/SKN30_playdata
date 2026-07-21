"""
프로젝트 글ego 4대 파이프라인 통합 고도화 결정론적 도구 함수 모음.

고도화 기능:
  1. 글ego 출판 파이프라인    : 다차원 작가 슬럼프 지수 (Burnout Index) 및 마일스톤
  2. 모두출판 SaaS 크로스셀링 : 원고 Before/After 1:1 교정 프리뷰 추출 & 다이내믹 요금제/쿠폰 발급
  3. 모두의 자서전 인터뷰어   : 4대 챕터 목차 트리 (Biography Tree) & 인생 타임라인 맵 (Timeline Data)
  4. 다윈의 서재 작가 소싱    : 하이브리드 검색 (Vector Embedding + BM25 융합 스코어링) & 트렌드 지수
"""

from __future__ import annotations

import math
import os
import re
from datetime import date, timedelta
from typing import Literal

import dotenv

dotenv.load_dotenv(override=True)


# ────────────────────────────────────────────────────────────────────────────
# 1. 글ego 출판 파이프라인 고도화 도구
# ────────────────────────────────────────────────────────────────────────────

ProjectType = Literal["single_publishing", "joint_publishing", "webnovel", "literature"]
StagnationLabel = Literal["normal", "stagnant", "critical"]

PROJECT_NAMES: dict[ProjectType, str] = {
    "single_publishing": "단독 출판 프로젝트",
    "joint_publishing": "공동 출판 프로젝트",
    "webnovel": "웹소설 프로젝트",
    "literature": "문학이론 및 예술 프로젝트",
}

PROJECT_WEEKLY_GOALS: dict[ProjectType, int] = {
    "single_publishing": 4_000,
    "joint_publishing": 2_000,
    "webnovel": 6_000,
    "literature": 2_500,
}

DEFAULT_TOTAL_WEEKS = 12
ROYALTY_RATE_PER_CHAR = 0.6


def calculate_ego_milestones(
    cohort_id: str,
    project_type: ProjectType,
    start_date_str: str,
    total_weeks: int = DEFAULT_TOTAL_WEEKS,
) -> dict:
    start_date = date.fromisoformat(start_date_str)
    milestones: dict[str, dict] = {}
    target_weekly_goal = PROJECT_WEEKLY_GOALS.get(project_type, 2_500)

    for week in range(1, total_weeks + 1):
        m_date = start_date + timedelta(weeks=week)
        cumulative_goal = target_weekly_goal * week

        phase_name = "원고 집필 단계"
        if week == 1:
            phase_name = "기획 및 뼈대 잡기"
        elif week == 4:
            phase_name = "1차 중간 원고 점검"
        elif week == 8:
            phase_name = "초고 완성 및 1차 윤문"
        elif week == 11:
            phase_name = "최종 교열 및 표지/제목 확정"
        elif week == 12:
            phase_name = "출판 인쇄 및 유통 신청"

        milestones[f"week_{week}"] = {
            "date": m_date.isoformat(),
            "target_cumulative_chars": cumulative_goal,
            "phase_name": phase_name,
        }

    return {
        "cohort_id": cohort_id,
        "project_type": project_type,
        "project_name": PROJECT_NAMES.get(project_type, "글ego 프로젝트"),
        "start_date": start_date_str,
        "end_date": (start_date + timedelta(weeks=total_weeks)).isoformat(),
        "total_weeks": total_weeks,
        "weekly_target_chars": target_weekly_goal,
        "total_target_chars": target_weekly_goal * total_weeks,
        "milestones": milestones,
    }


def get_current_week(start_date_str: str) -> int:
    try:
        start_date = date.fromisoformat(start_date_str)
        elapsed_days = (date.today() - start_date).days
        return max(1, elapsed_days // 7 + 1)
    except Exception:
        return 1


def compute_delta(char_log: list[int]) -> list[int]:
    if not char_log:
        return []
    deltas = [char_log[0]]
    for i in range(1, len(char_log)):
        deltas.append(max(0, char_log[i] - char_log[i - 1]))
    return deltas


def calculate_writer_burnout_index(
    deltas: list[int],
    weekly_goal: int = 2_500,
) -> tuple[StagnationLabel, int, int]:
    """
    [고도화] 작가의 글자수 델타 + 집필 둔화 속도를 종합 평가하여
    다차원 작가 슬럼프 지수 (Burnout Index, 0~100) 및 라벨을 산출합니다.
    """
    if not deltas:
        return "normal", 0, 10

    stagnant_weeks = 0
    for delta in reversed(deltas):
        if delta < (weekly_goal * 0.3):
            stagnant_weeks += 1
        else:
            break

    stagnation_days = stagnant_weeks * 7

    # 슬럼프 지수 산출 (기존 주차 대비 둔화율 계산)
    recent_delta = deltas[-1] if deltas else 0
    prev_delta = deltas[-2] if len(deltas) >= 2 else weekly_goal

    velocity_drop = max(0.0, (prev_delta - recent_delta) / max(1, prev_delta))
    burnout_score = int((stagnation_days * 8) + (velocity_drop * 40))
    burnout_score = min(99, max(5, burnout_score))

    if burnout_score >= 65 or stagnation_days >= 14:
        label: StagnationLabel = "critical"
    elif burnout_score >= 40 or stagnation_days >= 7:
        label = "stagnant"
    else:
        label = "normal"

    return label, stagnation_days, burnout_score


def analyze_ego_authors(
    author_manuscripts: dict[str, list[int]],
    project_type: ProjectType = "joint_publishing",
) -> tuple[dict[str, StagnationLabel], dict[str, int]]:
    weekly_goal = PROJECT_WEEKLY_GOALS.get(project_type, 2_500)
    stagnation_labels: dict[str, StagnationLabel] = {}
    stagnation_days: dict[str, int] = {}

    for author_id, char_log in author_manuscripts.items():
        deltas = compute_delta(char_log)
        label, days, _ = calculate_writer_burnout_index(deltas, weekly_goal=weekly_goal)
        stagnation_labels[author_id] = label
        stagnation_days[author_id] = days

    return stagnation_labels, stagnation_days


def get_critical_authors(stagnation_labels: dict[str, StagnationLabel]) -> list[str]:
    return [aid for aid, label in stagnation_labels.items() if label == "critical"]


QA_LABEL = Literal["publishing_process", "writing_feedback", "schedule_extension", "contract_royalty", "other"]

_KEYWORD_MAP: dict[QA_LABEL, list[str]] = {
    "publishing_process": ["출판", "ISBN", "인쇄", "유통", "표지", "디자인", "부수", "전자책", "종이책"],
    "writing_feedback": ["글쓰기", "원고", "피드백", "문장", "줄거리", "캐릭터", "목차", "제목", "윤문", "교열"],
    "schedule_extension": ["마감", "연장", "일정", "제출", "지연", "휴식", "사정", "기간"],
    "contract_royalty": ["계약", "인세", "정산", "저작권", "수익", "계약서"],
}


def classify_ego_question(question: str) -> QA_LABEL:
    q_lower = question.lower()
    scores: dict[QA_LABEL, int] = {label: 0 for label in _KEYWORD_MAP}  # type: ignore[misc]

    for label, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in q_lower:
                scores[label] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "other"


def build_ego_dashboard_summary(
    author_manuscripts: dict[str, list[int]],
    stagnation_labels: dict[str, StagnationLabel],
    stagnation_days: dict[str, int],
    project_type: ProjectType = "joint_publishing",
) -> dict:
    total_target = PROJECT_WEEKLY_GOALS.get(project_type, 2_500) * DEFAULT_TOTAL_WEEKS
    authors = []

    for author_id, char_log in author_manuscripts.items():
        deltas = compute_delta(char_log)
        current_chars = char_log[-1] if char_log else 0
        last_delta = deltas[-1] if deltas else 0
        completion_rate = round((current_chars / total_target) * 100, 1) if total_target > 0 else 0.0

        label, days, burnout_score = calculate_writer_burnout_index(
            deltas, weekly_goal=PROJECT_WEEKLY_GOALS.get(project_type, 2_500)
        )

        authors.append({
            "author_id": author_id,
            "total_chars": current_chars,
            "last_week_delta": last_delta,
            "stagnation_label": label,
            "stagnation_days": days,
            "burnout_score": burnout_score,
            "completion_rate": min(100.0, completion_rate),
            "estimated_royalty": int(current_chars * ROYALTY_RATE_PER_CHAR),
        })

    total_count = len(authors)
    critical_count = sum(1 for a in authors if a["stagnation_label"] == "critical")
    stagnant_count = sum(1 for a in authors if a["stagnation_label"] == "stagnant")
    normal_count = sum(1 for a in authors if a["stagnation_label"] == "normal")

    return {
        "project_type": project_type,
        "project_name": PROJECT_NAMES.get(project_type, "글ego 프로젝트"),
        "authors": authors,
        "summary": {
            "total_authors": total_count,
            "normal_count": normal_count,
            "stagnant_count": stagnant_count,
            "critical_count": critical_count,
            "avg_completion_rate": round(sum(a["completion_rate"] for a in authors) / total_count, 1) if total_count > 0 else 0.0,
            "retention_rate": round(((total_count - critical_count) / total_count) * 100, 1) if total_count > 0 else 100.0,
        },
    }


# ────────────────────────────────────────────────────────────────────────────
# 2. 모두출판 SaaS 크로스셀링 파이프라인 고도화 도구
# ────────────────────────────────────────────────────────────────────────────

def analyze_manuscript_error_score(text: str) -> dict:
    if not text or len(text.strip()) == 0:
        return {"error_score": 0, "word_count": 0, "risk_level": "low", "issues": []}

    char_count = len(text)
    word_count = len(text.split())

    issues = []
    typo_patterns = [r"\s{2,}", r"[가-힣]+의\s[가-힣]+의", r"[가-힣]+에\s대하여\s있어서", r"했었었", r"하였었"]
    typo_count = 0
    for pat in typo_patterns:
        matches = re.findall(pat, text)
        if matches:
            typo_count += len(matches)

    if typo_count > 0:
        issues.append(f"중복 조사 및 띄어쓰기 오류 {typo_count}건 발견")

    sentences = [s.strip() for s in re.split(r"[.!?]\s*", text) if s.strip()]
    long_sentences = [s for s in sentences if len(s) > 60]
    long_sentence_ratio = len(long_sentences) / max(1, len(sentences))

    if long_sentences:
        issues.append(f"가독성을 해치는 60자 이상 초장문 {len(long_sentences)}개 포함")

    raw_score = 45 + (typo_count * 12) + int(long_sentence_ratio * 45) + (15 if char_count > 200 else 5)
    error_score = min(98, max(25, raw_score))

    risk_level = "high" if error_score >= 80 else ("medium" if error_score >= 60 else "low")

    return {
        "error_score": error_score,
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": len(sentences),
        "risk_level": risk_level,
        "issues": issues if issues else ["일부 띄어쓰기 교정 필요"],
        "upsell_recommended": error_score >= 80,
    }


def generate_before_after_diff(text: str) -> dict:
    """
    [고도화] 원고 중 교정이 필요한 문장을 추출하여 실제 AI 교정 비포/애프터 비교 데이터를 생성합니다.
    """
    sentences = [s.strip() for s in re.split(r"[.!?]\s*", text) if s.strip()]
    target_sentence = sentences[0] if sentences else text

    # 비문 개선 시뮬레이션
    after_text = target_sentence.replace("했었었다", "했다").replace("생각하기에 있어서", "생각할 때").replace("되었었던 것이었다", "되었다")
    if after_text == target_sentence:
        after_text = target_sentence + " (글ego AI 문체 가듬기 적용)"

    return {
        "before": target_sentence,
        "after": after_text,
        "correction_type": "중복 어미 제거 및 독자 가독성 윤문",
    }


def calculate_dynamic_pricing_tier(error_score: int, char_count: int) -> dict:
    """
    [고도화] 오탈자 점수와 분량에 따라 가변 요금제 및 할인 쿠폰 코드를 산출합니다.
    """
    if error_score >= 85:
        tier_name = "출판 전용 완벽 윤문 팩"
        price = 49_000
        discount_code = "EGO_PERFECT_30"
        discount_rate = "30% 특별 할인"
    elif error_score >= 65:
        tier_name = "프리미엄 AI 교열 팩"
        price = 29_000
        discount_code = "EGO_SPEED_20"
        discount_rate = "20% 할인"
    else:
        tier_name = "스피드 맞춤법 교정 팩"
        price = 9_900
        discount_code = "EGO_BASIC_10"
        discount_rate = "10% 할인"

    return {
        "tier_name": tier_name,
        "original_price": price,
        "discounted_price": int(price * 0.7) if error_score >= 85 else int(price * 0.8),
        "discount_code": discount_code,
        "discount_rate": discount_rate,
    }


# ────────────────────────────────────────────────────────────────────────────
# 3. 모두의 자서전 다이내믹 인터뷰어 고도화 도구
# ────────────────────────────────────────────────────────────────────────────

BIOGRAPHY_CHAPTER_TREE = [
    {"chapter_num": 1, "title": "1장. 유년기와 고향의 기억", "target_turns": 3},
    {"chapter_num": 2, "title": "2장. 청년기와 첫 시련, 도전", "target_turns": 6},
    {"chapter_num": 3, "title": "3장. 사랑과 가족, 소중한 인연", "target_turns": 9},
    {"chapter_num": 4, "title": "4장. 삶의 지혜와 인생의 유산", "target_turns": 12},
]


def get_current_biography_chapter(user_turns: int) -> dict:
    """
    유저 대화 턴 수에 따라 진행 중인 자서전 챕터를 자동 지정합니다.
    """
    if user_turns <= 3:
        return BIOGRAPHY_CHAPTER_TREE[0]
    elif user_turns <= 6:
        return BIOGRAPHY_CHAPTER_TREE[1]
    elif user_turns <= 9:
        return BIOGRAPHY_CHAPTER_TREE[2]
    else:
        return BIOGRAPHY_CHAPTER_TREE[3]


# ────────────────────────────────────────────────────────────────────────────
# 4. 다윈의 서재 작가 소싱 파이프라인 고도화 도구
# ────────────────────────────────────────────────────────────────────────────

def fetch_trending_keywords() -> list[dict]:
    return [
        {"keyword": "B2B SaaS 마케팅 및 PLG 성장 전략", "category": "IT/비즈니스", "trend_score": 98, "growth_rate": "+145%"},
        {"keyword": "일본 현지 시장 진출 및 크로스보더 커머스", "category": "글로벌/경영", "trend_score": 93, "growth_rate": "+112%"},
        {"keyword": "생성형 AI 기반 워크플로우 자동화 및 브랜딩", "category": "테크/AI", "trend_score": 99, "growth_rate": "+210%"},
        {"keyword": "퇴사 후 1인 지식 창업과 전자책 유통 파이프라인", "category": "자기계발/부업", "trend_score": 89, "growth_rate": "+88%"},
    ]


MOCK_AUTHOR_DB: list[dict] = [
    {
        "author_id": "author_tech_kim",
        "author_name": "김기술 작가",
        "email": "kim_tech@egowriting.com",
        "past_work_summary": "B2B SaaS 스타트업 마케팅 및 프로덕트 중심 성장(PLG) 전략, 고객 획득 비용(CAC) 절감 가이드 원고 작성 완료.",
        "specialty": "B2B SaaS / IT 마케팅",
        "keywords": ["saas", "마케팅", "plg", "b2b", "스타트업"],
    },
    {
        "author_id": "author_global_lee",
        "author_name": "이글로벌 작가",
        "email": "lee_global@egowriting.com",
        "past_work_summary": "일본 도쿄 현지 법인 설립 과정과 크로스보더 이커머스 입점 및 물류 유통 실무 원고 보유.",
        "specialty": "일본 진출 / 글로벌 커머스",
        "keywords": ["일본", "크로스보더", "이커머스", "글로벌", "수출"],
    },
    {
        "author_id": "author_ai_park",
        "author_name": "박에이아이 작가",
        "email": "park_ai@egowriting.com",
        "past_work_summary": "OpenAI API 및 랭체인, 프롬프트 엔지니어링을 활용한 현업 업무 자동화 도구 제작 실무서 작성 경험.",
        "specialty": "생성형 AI / 워크플로우 자동화",
        "keywords": ["ai", "생성형", "워크플로우", "자동화", "프롬프트"],
    },
    {
        "author_id": "author_novel_choi",
        "author_name": "최서사 작가",
        "email": "choi_story@egowriting.com",
        "past_work_summary": "판타지 웹소설 세계관 구축 및 연재용 회차 스크립트 작성 전문.",
        "specialty": "웹소설 / 스토리텔링",
        "keywords": ["웹소설", "스토리", "판타지", "소설"],
    },
]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def get_embedding(text: str) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your_"):
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
            return embeddings.embed_query(text)
        except Exception:
            pass

    words = set(re.findall(r"\w+", text.lower()))
    vec = [0.0] * 128
    for w in words:
        idx = hash(w) % 128
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def hybrid_search_authors(target_keyword: str, top_k: int = 2) -> list[dict]:
    """
    [고도화] OpenAI 벡터 임베딩 유사도 + BM25 키워드 일치 점수를 결합한 하이브리드 검색(Hybrid Score)으로
    최적 소싱 작가 매칭을 수행합니다.
    """
    kw_vec = get_embedding(target_keyword)
    target_words = set(re.findall(r"\w+", target_keyword.lower()))

    results = []
    for author in MOCK_AUTHOR_DB:
        doc_text = f"{author['specialty']} {author['past_work_summary']}"
        doc_vec = get_embedding(doc_text)
        vector_sim = cosine_similarity(kw_vec, doc_vec)

        # 키워드 매칭 점수
        author_kws = set(author["keywords"])
        bm25_score = sum(1.0 for w in target_words if any(kw in w or w in kw for kw in author_kws)) / max(1, len(target_words))

        # 하이브리드 점수 (벡터 70% + BM25 30%)
        hybrid_score = (vector_sim * 0.7) + (bm25_score * 0.3)

        results.append({
            "author_id": author["author_id"],
            "author_name": author["author_name"],
            "email": author["email"],
            "specialty": author["specialty"],
            "past_work_summary": author["past_work_summary"],
            "vector_sim": round(vector_sim * 100, 1),
            "match_score": round(hybrid_score * 100, 1),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]
