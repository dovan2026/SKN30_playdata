import streamlit as st
import random

# 앱 제목 만들기
st.title('점메추요 !!!!!!!!')

# 음식 종류 선택하기
food_select = st.selectbox('어떤 게 당기시나요?',
                           ('한식','중식','일식','양식'))

# 예산 선택하기
money_selectbox = st.sidebar.selectbox("소지금은 얼마인가요?",
                                     ("10,000원", "12,000원", "14,000원"))

# 선택값에 따라 아이콘 표시
if money_selectbox == '10,000원':
    st.sidebar.title('😌')
elif money_selectbox == '12,000원':
    st.sidebar.title('☺️')
else:
    st.sidebar.title('😆')

# 매운 음식 가능 여부 선택하기

# 버튼을 누르면 조건에 맞는 메뉴 추천하기
food_menu = {'한식':['김밥', '비빔밥', '비빔면'],
             '중식':['짬뽕','짜장면','꿔바로우'],
             '일식':['초밥','스시','회전초밥'],
             '양식':['파스타','리조또','스테이크']}

st.header('결정적 선택‼️')

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('🔥 매운 거')
    if st.button('추천 1'):
        st.success(f'### {food_menu[food_select][0]}')
        st.balloons()

with col2:
    st.subheader('🌤️ 덜 매운 거')
    if st.button('추천 2'):
        st.success(f'### {food_menu[food_select][1]}')
        st.balloons()

with col3:
    st.subheader('❄️ 안 매운 거')
    if st.button('추천 3'):
        st.success(f'### {food_menu[food_select][2]}')
        st.balloons()
