
import streamlit as st
import requests
import pandas as pd

# FastAPI 서버 주소
FASTAPI_URL = "http://127.0.0.1:8005"

st.title("FastAPI 연동 Streamlit 프론트엔드")

# ------------------------ 1. 사용자 관리 ------------------------
st.header("사용자 관리")

# 사용자 목록 조회 함수
def get_users():
    try:
        response = requests.get(f"{FASTAPI_URL}/users/")
        response.raise_for_status()  # 200번대 상태 코드가 아닐 경우 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"사용자 목록 조회 실패: {e}")
        return []

# 사용자 목록 표시
st.subheader("사용자 목록")
if st.button("새로고침"):
    users = get_users()
    if users:
        df = pd.DataFrame(users)
        st.dataframe(df)

# 사용자 생성
st.subheader("새로운 사용자 생성")
with st.form("create_user_form"):
    new_name = st.text_input("이름")
    new_email = st.text_input("이메일")
    submitted = st.form_submit_button("생성")
    if submitted:
        if new_name and new_email:
            try:
                response = requests.post(f"{FASTAPI_URL}/users/?name={new_name}&email={new_email}")
                response.raise_for_status()
                st.success(f"사용자 '{new_name}' 생성 완료!")
            except requests.exceptions.RequestException as e:
                st.error(f"사용자 생성 실패: {e}")
        else:
            st.warning("이름과 이메일을 모두 입력해주세요.")

# 사용자 정보 수정
st.subheader("사용자 정보 수정")
with st.form("update_user_form"):
    update_user_id = st.number_input("수정할 사용자 ID", min_value=1, step=1)
    update_name = st.text_input("새 이름")
    update_email = st.text_input("새 이메일")
    submitted = st.form_submit_button("수정")
    if submitted:
        if update_name and update_email:
            try:
                response = requests.put(f"{FASTAPI_URL}/users/{update_user_id}?name={update_name}&email={update_email}")
                response.raise_for_status()
                st.success(f"사용자 ID {update_user_id} 정보 수정 완료!")
            except requests.exceptions.RequestException as e:
                st.error(f"사용자 수정 실패: {e}")
        else:
            st.warning("새 이름과 새 이메일을 모두 입력해주세요.")

# 사용자 삭제
st.subheader("사용자 삭제")
with st.form("delete_user_form"):
    delete_user_id = st.number_input("삭제할 사용자 ID", min_value=1, step=1)
    submitted = st.form_submit_button("삭제")
    if submitted:
        try:
            response = requests.delete(f"{FASTAPI_URL}/users/{delete_user_id}")
            response.raise_for_status()
            st.success(f"사용자 ID {delete_user_id} 삭제 완료!")
        except requests.exceptions.RequestException as e:
            st.error(f"사용자 삭제 실패: {e}")


# ------------------------ 2. 챗봇 ------------------------
st.header("챗봇과 대화하기")

chat_user_id = st.number_input("대화할 사용자 ID", min_value=1, step=1)
input_text = st.text_input("메시지 입력")

if st.button("전송"):
    if chat_user_id and input_text:
        try:
            response = requests.post(f"{FASTAPI_URL}/chatbot/{chat_user_id}?input_text={input_text}")
            response.raise_for_status()
            chat_response = response.json()
            
            st.text(f"나: {chat_response['input_text']}")
            st.text(f"AI: {chat_response['output_text']}")

        except requests.exceptions.RequestException as e:
            st.error(f"메시지 전송 실패: {e}")
    else:
        st.warning("사용자 ID와 메시지를 모두 입력해주세요.")

