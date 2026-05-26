import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px

# px 모듈이 없다고 에러가 나는 경우에는 plotly 라이브러리 설치
# Terminal > New terminal 선택 후, 가상환경에서 uv add plotly

# 1. simply chart
st.header('Unit 1. streamlit Simple chart')

chart_data = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_sales.csv')

st.subheader('1. Simple Line chart')
# use_container_width = 가로로 화면을 꽉 채워줌
st.line_chart(chart_data, use_container_width=True)

st.subheader('2. Simple Bar chart')
st.bar_chart(chart_data)

st.subheader('3. Simple area chart')
st.area_chart(chart_data)

# 2. Altair chart
st.header('Unit 2. Altair chart')

# 1) 리테일 매출 데이터 로드
df = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_retail.csv')

# melt로 나타내기
# id_vars : 그대로 유지할 식별자 컬럼
df_melted = pd.melt(df, id_vars=['date'], var_name='teams', value_name='sales')

# columns 메서드를 이용하여 좌-원본 데이터, 우- 변환 데이터 확인
col1, col2 = st.columns(2)
with col1:
    st.text('원본데이터-df')
    st.dataframe(df)
with col2:
    st.text('변환데이터-df_melted')
    st.dataframe(df_melted)
    