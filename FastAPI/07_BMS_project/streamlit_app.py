# streamlit_app.py
import streamlit as st
import requests

API_URL = 

st.title("📚 책 관리 시스템")

menu = st.sidebar.selectbox("메뉴를 선택하세요", ["책 등록", "책 목록", "책 삭제"])

# 책 등록
if menu == "책 등록":
    st.subheader("책 등록")
    title = st.text_input("책 제목")
    author = st.text_input("저자")
    year = st.text_input("출판 연도")

    if st.button("등록하기"):
        if not title or not author or not year:
            st.warning("모든 필드를 입력해주세요.")
        else:
            with st.spinner("서버에 등록 중..."):
                try:
                    payload = {"title": title, "author": author, "publisher_year": year}
                    


                except requests.exceptions.RequestException as e:
                    st.error(f"서버 연결 실패: {e}")

# 책 목록
elif menu == "책 목록":
    st.subheader("책 목록")
    with st.spinner("목록을 불러오는 중..."):
        try:
            response = 
            if response.status_code ==:
                books = 
                if not books:
                    st.info("등록된 책이 없습니다.")
                for book in books:
                    st.write(f"📘 **ID**: {book['id']} | **제목**: {book['title']} | **저자**: {book['author']} | **출판연도**: {book['publisher_year']}")
            else:
                st.error(f"불러오기 실패! 상태 코드: { }")
        except requests.exceptions.RequestException as e:
            st.error(f"서버 연결 실패: {e}")

# 책 삭제
elif menu == "책 삭제":
    st.subheader("책 삭제")
    book_id = st.number_input("삭제할 책 ID 입력", min_value=1, step=1)
    if st.button("삭제하기"):
        with st.spinner("삭제 요청 중..."):
            try:
                response = 
                if response.status_code == :
                    st.success("책이 삭제되었습니다!")
                    st.toast("책 삭제 완료", icon="🗑️")
                else:
                    st.error(f"삭제 실패! 상태 코드: {}")
            except requests.exceptions.RequestException as e:
                st.error(f"서버 연결 실패: {e}")
