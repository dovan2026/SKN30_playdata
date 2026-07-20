"""노드에서 사용하는 LLM과 역할별 시스템 프롬프트."""


from functools import lru_cache
import os

import dotenv
from langchain_openai import ChatOpenAI

dotenv.load_dotenv(override=True)


PLANNER_SYSTEM_PROMPT = """
당신은 콘텐츠 기획자입니다.
주어진 주제에 대한 블로그 기사를 기획하고, 독자가 정보를 배우고 합리적인
결정을 내릴 수 있도록 돕는 자료를 구성합니다. 콘텐츠 작가가 바로 사용할 수
있는 상세한 개요, 관련 주제와 하위 주제를 준비하세요.
""".strip()

WRITER_SYSTEM_PROMPT = """
당신은 콘텐츠 작가입니다.
콘텐츠 기획자가 제공한 계획의 목표와 방향을 따라 통찰력 있고 사실적인 의견
기사를 작성하세요. 객관적 사실과 의견을 구분하고, 균형 잡힌 관점을 유지하세요.
""".strip()

EDITOR_SYSTEM_PROMPT = """
당신은 블로그 편집자입니다.
작성된 게시물이 좋은 저널리즘과 블로그 글쓰기 관행을 따르도록 교정하세요.
문법, 문체, 논리 전개를 다듬고 주장에는 균형 잡힌 관점이 드러나게 하세요.
""".strip()

TRANSLATOR_SYSTEM_PROMPT = """
당신은 전문 번역가이자 요약 편집자입니다.
입력 언어를 감지하고 핵심 의미와 글의 흐름을 보존하면서 자연스러운 한국어
콘텐츠로 작성하세요.
""".strip()


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """환경변수 설정으로 ChatOpenAI 인스턴스를 한 번만 생성합니다."""

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0.2,
    )


def _message_text(message: object) -> str:
    """문자열 또는 콘텐츠 블록 형식의 모델 응답을 문자열로 변환합니다."""

    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
        if text_parts:
            return "\n".join(text_parts)

    return str(content)


def run_agent(system_prompt: str, task_prompt: str) -> str:
    """역할 설명과 작업 지시를 모델에 전달하고 텍스트 결과를 반환합니다."""

    response = get_llm().invoke(
        [
            ("system", system_prompt),
            ("human", task_prompt)
        ]

    )

    return _message_text(response)
