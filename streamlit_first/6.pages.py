import streamlit as st

st.caption('text 참고사이트: https://docs.streamlit.io/library/api-multi-page-apps')

# 페이시 선언
def main_page():
    st.title('Main page 🐪')
    st.sidebar.title('Side main 🐪')
def page2():
    st.title('Page 2 🐶')
    st.sidebar.title('Side 2 🐶')
def page3():
    st.title('Page 3 🦉')
    st.sidebar.title('Side 3 🦉')

# 딕셔너리 선언
page_names_to_funcs = {"Main page" : main_page, 'Page 2': page2, 'Page 3': page3}

selected_age = st.sidebar.selectbox('select a page', page_names_to_funcs.keys())

# 해당 페이지 부르기
page_names_to_funcs[selected_age]()
