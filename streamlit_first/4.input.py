import streamlit as st
from datetime import datetime
import pandas as pd

st.title('Input Widgets')
st.caption('text 참고사이트: https://docs.streamlit.io/library/api-reference/widgets')

#1. 버튼
st.header('1.Button')

#버튼 클릭 시 실행
if st.button('노크하기'):
    st.write('여기 사람 있어요!!')
#버튼에 따른 조건문 처리
if st.button('Say hello'):
    st.write('hello')
else:
    st.write('Goodbye')

#2. 라디오 버튼
st.header('2.Radio Button')
genre = st.radio('좋아하는 영화 장르는?', ('SF', '액션','로맨스'))

if genre == 'SF':
    st.write('인터스텔라')
elif genre == '액션':
    st.write('테이큰;')
elif genre == '로맨스':
    st.write('말할 수 없는 비밀')

#3. 체크박스
st.header('3. Checkbox')
agree = st.checkbox('I agree')
if agree:
    st.write('🎥'*10)

#4, Selectbox(단일 선택)
st.header('4. Selectbox')
option = st.selectbox('어떻게 연락드릴까요?',
                      ('Email', 'Mobile', 'Office [phone]'))
st.write('네', option, '로 연락 드리겠습니다.')

#5 Multiselect(다중 선택)
st.header('5.multi select')
options = st.multiselect('좋아하는 색은?',
                        ['Green','Yellow','Red','Blue'], # 선택지
                        ['Yellow'] #기본 선택값
)


st.write('당신의 선호 색상은 :')
for i in options:
    st.write(i)

# 6. Input: Text/ Number
st.header('6. Input: Text/Number')

# 텍스트 입력
st.subheader('**_text_input_**')
title = st.text_input('가장 좋아하는 영화는?', 'Sound of Music')
st.write('당신의 최애 영화는:', title)

# 숫자 입력
st.subheader('**_number_input_**')
number = st.number_input('Insert a number(1-10)', min_value=1, max_value=10, value=5, step=1)
st.write('The current number is', number)

# 7. Date input
st.header('7.Date input')
ymd = st.date_input('When is your birthday', datetime(2000,9,6))
st.write('Your Birthday', ymd)

# 8. slider
st.header('8.Slider')

# 숫자 글라이더 (단일 값)
st.subheader('**_Slider-이전 구간_**')
age = st.slider('나이가 어떻게 되세요?', 0, 130, 25)
values = st.slider('값 구간을 선택하세요', 0.0, 100.0, (25.0,75.0))
st.write('values:', values)

# 날짜 구간 슬라이더
st.subheader('년 월 일 사이 구간')

slider_date = st.slider(
    '날짜 구간을 선택하세요.',
    min_value = datetime(2024,1,1),
    max_value = datetime(2024,12,31),
    value = (datetime(2024,6,1), datetime(2024,7,31)),
    format = 'YY/MM/DD'
)
st.write('slider date:', slider_date)
st.write('slider_date[0]:', slider_date[0], 'slider_date[1]:', slider_date[1])

# 날짜 구간으로 데이터 조회하기
st.header('날짜 구간으로 데이터 조회하기')

# csv 데이터 불러와