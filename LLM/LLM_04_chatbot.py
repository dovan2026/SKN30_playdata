import base64
import os
import time
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_openai_api_key():
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


api_key = get_openai_api_key()
if not api_key:
    st.error("Set OPENAI_API_KEY in .streamlit/secrets.toml or .env.")
    st.stop()

client = OpenAI(api_key=api_key)

def answer_generator(prompt):
    with client.responses.stream(
        model="gpt-5.1-mini",
        instructions="너는 게임 속 강아지 NPC다. 말끝에 가끔 '멍'을 붙이고 짧게 답한다. Halㅣucination(환각)은 금지다.",
        input=[
            {"role": "user", "content": prompt}
        ],
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta


st.title("멍챗봇 🐶")

# 메시지 상태 초기화 및 시스템 메시지 추가
if "messages" not in st.session_state:
    st.session_state.messages = []
    system_message = '역할: 너는 이제부터 게임 NPC다. 자신을 실제 게임속 인간이라고 생각한다.'
    system_message += '목적: 실제 사람처럼 대화하는 게임 NPC 모드'
    system_message += '표현: 강아지처럼 말 끝마다 "멍"을 붙인다. 항상 50글자 이내로 답변한다.'
    st.session_state.messages.append({"role": "system", "content": system_message})

# 메시지 출력 (시스템 메시지는 제외)
messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
for message in st.session_state.messages:
    if message["role"] != "system":  # 시스템 메시지는 출력하지 않음
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("프롬프트를 입력하세요."):
    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 어시스턴트 응답 생성 및 출력
    with st.chat_message("assistant"):
        response = st.write_stream(answer_generator(prompt))

    st.session_state.messages.append({"role": "assistant", "content": response})
 
