# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("📚 책 관리 시스템")

menu = st.sidebar.selectbox(
    "메뉴를 선택하세요",
    ["책 등록", "책 목록", "책 검색", "책 수정", "책 삭제"],    # 실습 : 책 수정, 책 검색 추가
)


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
                    response = requests.post(f"{API_URL}/books/", json=payload)
                    # FastAPI의 POST /books/는 생성 성공 시 201 Created를 반환함.
                    if response.status_code == 201:
                        st.success("책이 성공적으로 등록되었습니다.!!")
                        st.toast("새 책이 등록되었습니다.", icon="✅")
                    else:
                        st.error(f"등록 실패! 상태 코드 : {response.status_code}")      
                except requests.exceptions.RequestException as e:
                    st.error(f"서버 연결 실패: {e}")

# 책 목록
elif menu == "책 목록":
    st.subheader("책 목록")
    with st.spinner("목록을 불러오는 중..."):
        try:
            response = requests.get(f"{API_URL}/books/")
            if response.status_code == 200:
                books = response.json()
                if not books:
                    st.info("등록된 책이 없습니다.")
                for book in books:
                    st.write(f"📘 **ID**: {book['id']} | **제목**: {book['title']} | **저자**: {book['author']} | **출판연도**: {book['publisher_year']}")
            else:
                st.error(f"불러오기 실패! 상태 코드: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"서버 연결 실패: {e}")

# 실습 : 책 검색
elif menu == "책 검색":
    st.subheader("책 검색")

    keyword = st.text_input(
        "검색어",
        placeholder="책 제목 또는 저자를 입력하세요.",
    )

    if st.button("검색하기"):
        # 공백만 입력한 경우도 빈 검색어로 처리합니다.
        keyword = keyword.strip()

        if not keyword:
            st.warning("검색어를 입력해주세요.")

        else:
            with st.spinner("책을 검색하는 중..."):
                try:
                    response = requests.get(
                        f"{API_URL}/books/search",
                        params={"keyword": keyword},
                    )

                    if response.status_code == 200:
                        books = response.json()

                        if not books:
                            st.info("검색 결과가 없습니다.")

                        else:
                            st.success(
                                f"{len(books)}권의 책을 찾았습니다."
                            )

                            for book in books:
                                st.write(
                                    f"📘 ID: {book['id']} | "
                                    f"제목: {book['title']} | "
                                    f"저자: {book['author']} | "
                                    f"출판 연도: "
                                    f"{book['publisher_year']}"
                                )

                    elif response.status_code == 422:
                        st.error("검색어가 올바르지 않습니다.")

                    else:
                        st.error(
                            f"검색 실패! 상태 코드: "
                            f"{response.status_code}"
                        )

                except requests.exceptions.RequestException as e:
                    st.error(f"서버 연결 실패: {e}")


# 실습 : 책 수정
elif menu == "책 수정":
    st.subheader("책 정보 수정")

    book_id = st.number_input(
        "수정할 책 ID",
        min_value=1,
        step=1,
    )

    title = st.text_input("수정할 책 제목")
    author = st.text_input("수정할 저자")
    year = st.text_input("수정할 출판 연도")

    if st.button("수정하기"):
        # 모든 필드가 입력되었는지 확인합니다.
        if not title or not author or not year:
            st.warning("모든 필드를 입력해주세요.")

        else:
            payload = {
                "title": title,
                "author": author,
                "publisher_year": year,
            }

            with st.spinner("책 정보를 수정하는 중..."):
                try:
                    response = requests.put(
                        f"{API_URL}/books/{book_id}",
                        json=payload,
                    )

                    if response.status_code == 200:
                        updated_book = response.json()

                        st.success("책 정보가 수정되었습니다!")
                        st.write(f"ID: {updated_book['id']}")
                        st.write(f"제목: {updated_book['title']}")
                        st.write(f"저자: {updated_book['author']}")
                        st.write(
                            f"출판 연도: "
                            f"{updated_book['publisher_year']}"
                        )

                    elif response.status_code == 404:
                        st.error("해당 ID의 책을 찾을 수 없습니다.")

                    elif response.status_code == 422:
                        st.error("입력값이 올바르지 않습니다.")

                    else:
                        st.error(
                            f"수정 실패! 상태 코드: "
                            f"{response.status_code}"
                        )

                except requests.exceptions.RequestException as e:
                    st.error(f"서버 연결 실패: {e}")


# 책 삭제
elif menu == "책 삭제":
    st.subheader("책 삭제")
    book_id = st.number_input("삭제할 책 ID 입력", min_value=1, step=1)
    if st.button("삭제하기"):
        with st.spinner("삭제 요청 중..."):
            try:
                response = requests.delete(f"{API_URL}/books/{book_id}")
                if response.status_code == 200:
                    st.success("책이 삭제되었습니다!")
                    st.toast("책 삭제 완료", icon="🗑️")
                else:
                    st.error(f"삭제 실패! 상태 코드: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"서버 연결 실패: {e}")


