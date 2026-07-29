import os
import re
import textwrap
from io import BytesIO
from pathlib import Path

import matplotlib
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle


load_dotenv(override=True)

st.set_page_config(
    page_title="지옥면접 AI 면접관",
    layout="centered",
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_VALID_ANSWERS = 10
SCORE_ITEMS = ["논리성", "구체성", "전달력", "직무 적합도", "문제 해결력", "자기 성찰"]

model = ChatOpenAI(
    model=MODEL,
    temperature=0.7,
    timeout=120,
    max_retries=3,
)

parser = StrOutputParser()

INTERVIEW_SYSTEM_PROMPTS = {
    "인성 면접": """
지원자의 태도, 협업 방식, 갈등 해결, 책임감, 성장 가능성을 검증한다.
경험의 진정성, 행동의 일관성, 조직 적응 가능성을 집요하게 확인한다.
""",
    "프로젝트 면접": """
지원자의 프로젝트 경험, 문제 정의, 기술 선택 이유, 본인 역할, 성과, 실패 회고를 검증한다.
추상적인 답변에는 구체적인 상황, 수치, 의사결정 근거를 요구한다.
""",
    "기술 면접": """
지원자의 CS 전공지식, 파이썬 알고리즘, 시스템 설계 기초, 기술적 판단력을 검증한다.
부정확한 설명에는 반례나 추가 조건을 던져 이해 깊이를 확인한다.
""",
    "임원 면접": """
지원자의 커리어 방향, 조직 적합성, 비즈니스 이해도, 의사결정 방식, 장기 성장 가능성을 검증한다.
지원자의 말과 회사/팀의 현실 사이에 모순이 없는지 확인한다.
""",
}

INTERVIEWER_PERSONAS = {
    "압박형": """
말투는 날카롭지만 무례하지 않다.
지원자의 답변에서 빈틈을 찾아 꼬리질문을 이어간다.
왜, 어떻게, 본인이 한 일, 결과를 반복해서 확인한다.
답변이 좁거나 자기중심적이면 시야가 부족하다고 지적한다.
""",
    "코치형": """
말투는 차분하고 교육적이다.
부족한 답변도 먼저 핵심을 정리해준 뒤 개선 질문을 던진다.
압박 강도는 낮지만 평가 기준은 명확하다.
""",
    "실무형": """
말투는 간결하고 실무 중심적이다.
근거 없는 주장, 과장, 모호한 표현을 바로 지적한다.
답변의 실행 가능성과 실제 기여도를 중점적으로 따진다.
""",
}

SCORE_RUBRIC = """
답변 평가는 반드시 아래 6개 기준으로 0~10점을 매긴다.
- 논리성: 주장과 근거가 자연스럽게 이어지는가
- 구체성: 실제 경험, 수치, 상황, 행동이 구체적인가
- 전달력: 핵심이 간결하고 이해하기 쉬운가
- 직무 적합도: 지원 직무와 연결되는 역량이 드러나는가
- 문제 해결력: 문제를 정의하고 해결한 과정이 설득력 있는가
- 자기 성찰: 배운 점과 개선 방향을 말할 수 있는가
"""


def make_interview_chain(interview_type: str, interview_focus: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
너는 IT 회사의 {interview_type} 면접관이다.

지원 직무:
{{job_role}}

면접 유형 목표:
{interview_focus}

면접관 성격:
{{interviewer_persona}}

평가 기준:
{SCORE_RUBRIC}

진행 규칙:
1. 이전 대화 기록을 기억하고, 지원자의 이전 답변을 바탕으로 꼬리질문을 이어간다.
2. 한 번에 질문은 하나만 한다.
3. 첫 질문 요청을 받으면 평가 없이 첫 질문만 한다.
4. 지원자 답변 평가 요청을 받으면 반드시 아래 형식을 지킨다.
5. 답변이 부족하면 무엇이 부족한지 짧게 지적하고 더 구체적인 꼬리질문을 던진다.
6. 10번째 답변 평가 요청이면 다음 질문 없이 마지막 답변 피드백만 작성한다.

답변 평가 형식:
### 답변 평가
- 논리성: n/10
- 구체성: n/10
- 전달력: n/10
- 직무 적합도: n/10
- 문제 해결력: n/10
- 자기 성찰: n/10
- 종합 점수: n/60

### 피드백
지원자의 강점과 부족한 점을 3~5문장으로 평가한다.

### 모범 답변 예시
30년차 IT 전문가가 실무 면접 코칭을 해주는 말투로 작성한다.
먼저 "이렇게 답하면 더 좋습니다."라고 짧게 짚고, 지원자가 실제 면접에서 말할 수 있는 개선 답변을 4~6문장으로 제시한다.
답변에는 구체적 상황, 본인 행동, 판단 근거, 결과, 배운 점이 자연스럽게 들어가야 한다.

### 다음 질문
다음 질문을 하나만 제시한다. 단, 10번째 답변이면 "면접이 종료되었습니다."라고 적는다.
""",
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    return prompt | model | parser


interview_chains = {
    interview_type: make_interview_chain(interview_type, system_prompt)
    for interview_type, system_prompt in INTERVIEW_SYSTEM_PROMPTS.items()
}

report_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f"""
너는 IT 회사의 최종 면접 평가관이다.
면접 대화 기록과 답변별 평가를 바탕으로 최종 리포트를 작성한다.
반드시 사용자가 지정한 개요를 지킨다.
한국어로 작성한다.

평가 기준:
{SCORE_RUBRIC}
""",
        ),
        (
            "human",
            """
지원 직무:
{job_role}

면접 종류:
{interview_type}

면접관 성격:
{interviewer_style}

면접 대화 기록:
{history_text}

답변별 평가 기록:
{evaluation_text}

아래 형식으로 최종 보고서를 작성해줘.

- 면접 종류:
- 답변 중 Best:
- 답변 중 Worst:
- 면접 상세 피드백:
- 결론:
""",
        ),
    ]
)

report_chain = report_prompt | model | parser


def reset_interview() -> None:
    st.session_state.messages = []
    st.session_state.evaluations = []
    st.session_state.valid_answer_count = 0
    st.session_state.report = None


def get_history_text() -> str:
    return "\n\n".join(
        f"{'지원자' if isinstance(message, HumanMessage) else '면접관'}: {message.content}"
        for message in st.session_state.messages
    )


def get_evaluation_text() -> str:
    return "\n\n".join(st.session_state.evaluations) or "아직 평가 기록 없음"


def strip_score_text(text: str) -> str:
    hidden_line_pattern = re.compile(
        rf"^\s*-?\s*({'|'.join(re.escape(item) for item in SCORE_ITEMS)}|종합\s*점수)\s*[:：]\s*"
        r"\d+(?:\.\d+)?\s*/\s*(?:10|60)\s*$"
    )
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "### 답변 평가":
            continue
        if hidden_line_pattern.match(stripped):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_latest_scores() -> tuple[dict[str, float], float]:
    if not st.session_state.evaluations:
        return {item: 0.0 for item in SCORE_ITEMS}, 0.0

    latest_evaluation = st.session_state.evaluations[-1]
    scores = {}
    for item in SCORE_ITEMS:
        pattern = rf"{re.escape(item)}\s*[:：]\s*(\d+(?:\.\d+)?)\s*/\s*10"
        match = re.search(pattern, latest_evaluation)
        scores[item] = float(match.group(1)) if match else 0.0

    total_match = re.search(r"종합\s*점수\s*[:：]\s*(\d+(?:\.\d+)?)\s*/\s*60", latest_evaluation)
    total_score = float(total_match.group(1)) if total_match else sum(scores.values())
    return scores, total_score


def render_score_panel() -> None:
    if not st.session_state.evaluations:
        return

    scores, total_score = extract_latest_scores()
    answer_no = st.session_state.valid_answer_count
    total_percent = min(max(total_score / 60 * 100, 0), 100)

    gauge_rows = []
    for label, score in scores.items():
        percent = min(max(score / 10 * 100, 0), 100)
        gauge_rows.append(
            textwrap.dedent(
                f"""
                <div class="score-row">
                  <div class="score-label">
                    <span>{label}</span>
                    <strong>{score:g}/10</strong>
                  </div>
                  <div class="gauge-track">
                    <div class="gauge-fill" style="width: {percent:.1f}%"></div>
                  </div>
                </div>
                """
            ).strip()
        )

    latest_label = f"답변 {answer_no} 평가" if answer_no else "아직 평가 없음"
    panel_html = textwrap.dedent(
        f"""
        <style>
        .right-score-panel {{
          position: fixed;
          top: 5.5rem;
          right: 1.25rem;
          width: 300px;
          max-height: calc(100vh - 7rem);
          overflow-y: auto;
          z-index: 999;
          padding: 18px 18px 16px;
          border-radius: 8px;
          background: #fffaf3;
          border: 1px solid #fed7aa;
          box-shadow: 0 14px 36px rgba(31, 41, 55, 0.16);
          color: #1f2937;
        }}
        .right-score-panel h3 {{
          margin: 0;
          font-size: 18px;
          line-height: 1.25;
        }}
        .right-score-panel .panel-subtitle {{
          margin: 6px 0 14px;
          font-size: 12px;
          color: #6b7280;
        }}
        .score-row {{
          margin: 13px 0;
        }}
        .score-label {{
          display: flex;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 6px;
          font-size: 13px;
        }}
        .score-label strong {{
          font-size: 13px;
          color: #c2410c;
        }}
        .gauge-track {{
          height: 10px;
          border-radius: 999px;
          background: #ffedd5;
          overflow: hidden;
        }}
        .gauge-fill {{
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(90deg, #fb923c, #ea580c);
        }}
        .total-card {{
          margin-top: 16px;
          padding: 12px;
          border-radius: 8px;
          background: #f97316;
          color: white;
        }}
        .total-card .total-label {{
          font-size: 12px;
          opacity: 0.9;
        }}
        .total-card .total-score {{
          margin-top: 2px;
          font-size: 24px;
          font-weight: 800;
        }}
        .total-card .total-track {{
          margin-top: 9px;
          height: 8px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.34);
          overflow: hidden;
        }}
        .total-card .total-fill {{
          height: 100%;
          border-radius: 999px;
          background: white;
        }}
        @media (max-width: 1250px) {{
          .right-score-panel {{
            position: static;
            width: auto;
            max-height: none;
            margin: 1rem 0;
          }}
        }}
        </style>
        <div class="right-score-panel">
          <h3>답변 점수 게이지</h3>
          <div class="panel-subtitle">{latest_label}</div>
          {' '.join(gauge_rows)}
          <div class="total-card">
            <div class="total-label">종합 점수</div>
            <div class="total-score">{total_score:g}/60</div>
            <div class="total-track">
              <div class="total-fill" style="width: {total_percent:.1f}%"></div>
            </div>
          </div>
        </div>
        """
    ).strip()

    if hasattr(st, "html"):
        st.html(panel_html)
    else:
        st.markdown(
            panel_html,
            unsafe_allow_html=True,
        )


def get_korean_font() -> fm.FontProperties:
    font_candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
        Path("C:/Windows/Fonts/NanumGothic.ttf"),
    ]
    for font_path in font_candidates:
        if font_path.exists():
            return fm.FontProperties(fname=str(font_path))
    return fm.FontProperties()


def wrap_pdf_text(text: str, width: int = 46) -> list[str]:
    wrapped_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(line, width=width) or [""])
    return wrapped_lines


def create_report_pdf(
    report_text: str,
    job_role: str,
    interview_type: str,
    interviewer_style: str,
) -> bytes:
    orange = "#f97316"
    white = "#fffaf3"
    dark = "#1f2937"
    muted = "#6b7280"
    font = get_korean_font()
    pdf_buffer = BytesIO()

    header_lines = [
        "지옥면접 AI 면접 평가 리포트",
        f"지원 직무: {job_role}",
        f"면접 종류: {interview_type}",
        f"면접관 성격: {interviewer_style}",
    ]
    body_lines = wrap_pdf_text(report_text, width=48)
    first_page_lines = 26
    other_page_lines = 32
    pages = [body_lines[:first_page_lines]]
    for start in range(first_page_lines, len(body_lines), other_page_lines):
        pages.append(body_lines[start : start + other_page_lines])
    if not pages:
        pages = [[]]

    with PdfPages(pdf_buffer) as pdf:
        for page_index, page_lines in enumerate(pages, start=1):
            fig = plt.figure(figsize=(8.27, 11.69), facecolor=orange)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_axis_off()

            ax.add_patch(
                Rectangle(
                    (0.09, 0.055),
                    0.82,
                    0.89,
                    transform=ax.transAxes,
                    facecolor=white,
                    edgecolor="none",
                )
            )

            y = 0.89
            if page_index == 1:
                fig.text(
                    0.14,
                    y,
                    header_lines[0],
                    fontproperties=font,
                    fontsize=19,
                    weight="bold",
                    color=dark,
                )
                y -= 0.045
                for meta in header_lines[1:]:
                    fig.text(
                        0.14,
                        y,
                        meta,
                        fontproperties=font,
                        fontsize=10.5,
                        color=muted,
                    )
                    y -= 0.027
                y -= 0.02
            else:
                fig.text(
                    0.14,
                    y,
                    "지옥면접 AI 면접 평가 리포트",
                    fontproperties=font,
                    fontsize=14,
                    weight="bold",
                    color=dark,
                )
                y -= 0.055

            for line in page_lines:
                if line.startswith("- "):
                    fig.text(
                        0.14,
                        y,
                        line,
                        fontproperties=font,
                        fontsize=11,
                        weight="bold",
                        color=dark,
                    )
                else:
                    fig.text(
                        0.14,
                        y,
                        line,
                        fontproperties=font,
                        fontsize=10.2,
                        color=dark,
                    )
                y -= 0.023 if line else 0.018

            fig.text(
                0.5,
                0.075,
                f"{page_index} / {len(pages)}",
                fontproperties=font,
                fontsize=9,
                color=muted,
                ha="center",
            )
            pdf.savefig(fig, facecolor=fig.get_facecolor())
            plt.close(fig)

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def make_pdf_filename(interview_type: str, job_role: str) -> str:
    raw_filename = f"interview_report_{interview_type}_{job_role}.pdf"
    return "".join(
        char if char.isalnum() or char in "._-" else "_"
        for char in raw_filename
    )


for key, default in {
    "messages": [],
    "evaluations": [],
    "valid_answer_count": 0,
    "report": None,
    "settings_signature": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.sidebar.title("면접 설정")

job_role = st.sidebar.text_input("지원 직무", value="SQL 전문가").strip()
selected_type = st.sidebar.radio(
    "면접 유형",
    ["인성 면접", "프로젝트 면접", "기술 면접", "임원 면접"],
)
interviewer_style = st.sidebar.selectbox(
    "면접관 성격",
    ["압박형", "코치형", "실무형"],
)

settings_signature = (job_role, selected_type, interviewer_style)

if st.session_state.settings_signature is None:
    st.session_state.settings_signature = settings_signature

if st.session_state.settings_signature != settings_signature:
    st.session_state.settings_signature = settings_signature
    reset_interview()

if st.sidebar.button("면접 초기화"):
    reset_interview()
    st.rerun()

answer_count_placeholder = st.sidebar.empty()


def render_answer_count_metric() -> None:
    answer_count_placeholder.metric(
        "유효 답변 횟수",
        f"{st.session_state.valid_answer_count}/{MAX_VALID_ANSWERS}",
    )


render_answer_count_metric()
st.sidebar.caption(f"모델: {MODEL}")

st.title("AI 면접관을 골라봐!")
st.caption(f"{job_role or '지원 직무 미입력'} · {selected_type} · {interviewer_style}")

if not job_role:
    st.warning("좌측 사이드바에서 지원 직무를 먼저 입력하세요.")
    render_score_panel()
    st.stop()

if not st.session_state.messages:
    st.info("설정을 확인한 뒤 첫 질문을 받아 면접을 시작하세요.")
    if st.button("첫 질문 받기", type="primary"):
        with st.chat_message("assistant"):
            placeholder = st.empty()
            first_question = ""
            for chunk in interview_chains[selected_type].stream(
                {
                    "job_role": job_role,
                    "interviewer_persona": INTERVIEWER_PERSONAS[interviewer_style],
                    "history": [],
                    "input": "면접을 시작해 주세요. 지원 직무에 맞는 첫 질문 하나만 해 주세요.",
                }
            ):
                first_question += chunk
                placeholder.markdown(first_question)

        st.session_state.messages.append(AIMessage(content=first_question))
        st.rerun()

for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    else:
        with st.chat_message("assistant"):
            st.markdown(strip_score_text(message.content))

if st.session_state.report:
    st.divider()
    st.subheader("최종 면접 평가 리포트")
    st.markdown(st.session_state.report)
    pdf_bytes = create_report_pdf(
        st.session_state.report,
        job_role,
        selected_type,
        interviewer_style,
    )
    st.download_button(
        "주황 리포트 PDF 다운로드",
        data=pdf_bytes,
        file_name=make_pdf_filename(selected_type, job_role),
        mime="application/pdf",
        type="primary",
    )
    render_answer_count_metric()
    render_score_panel()
    st.stop()

if st.session_state.messages and st.session_state.valid_answer_count < MAX_VALID_ANSWERS:
    user_input = st.chat_input("답변을 입력하세요")

    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))

        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.valid_answer_count += 1
        answer_no = st.session_state.valid_answer_count
        is_last_answer = answer_no >= MAX_VALID_ANSWERS

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            request_text = (
                f"지원자의 마지막 답변을 평가해 주세요. "
                f"이번 답변은 {answer_no}/{MAX_VALID_ANSWERS}번째 유효 답변입니다. "
            )
            if is_last_answer:
                request_text += "10번째 답변이므로 다음 질문 없이 마지막 피드백만 작성해 주세요."
            else:
                request_text += "평가 후 이전 답변을 바탕으로 꼬리질문 하나를 이어서 해 주세요."

            for chunk in interview_chains[selected_type].stream(
                {
                    "job_role": job_role,
                    "interviewer_persona": INTERVIEWER_PERSONAS[interviewer_style],
                    "history": st.session_state.messages,
                    "input": request_text,
                }
            ):
                full_response += chunk
                display_response = strip_score_text(full_response)
                placeholder.markdown(display_response or "평가를 생성하는 중입니다...")

        cleaned_response = strip_score_text(full_response)
        st.session_state.messages.append(AIMessage(content=cleaned_response))
        st.session_state.evaluations.append(f"[답변 {answer_no}]\n{full_response}")

        if is_last_answer:
            with st.spinner("최종 면접 평가 리포트를 생성하는 중입니다."):
                st.session_state.report = report_chain.invoke(
                    {
                        "job_role": job_role,
                        "interview_type": selected_type,
                        "interviewer_style": interviewer_style,
                        "history_text": get_history_text(),
                        "evaluation_text": get_evaluation_text(),
                    }
                )
            st.rerun()

elif st.session_state.valid_answer_count >= MAX_VALID_ANSWERS:
    st.info("총 10개의 유효 답변이 완료되어 최종 리포트가 생성되었습니다.")

render_answer_count_metric()
render_score_panel()
