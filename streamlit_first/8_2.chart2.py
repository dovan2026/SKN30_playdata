import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px

st.title('심화문제')

st.subheader('1. Altair Scatter chart- 재무분석')

fi = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_financial.csv', encoding='CP949')


if st.checkbox('재무분석 데이터 조회'):
    st.dataframe(fi)


sel = st.radio('총매출 대비 분석을 원하는 항목을 선택하세요.',('판매량', '매출원가', '수익'))
if sel == '판매량' :
    chart = alt.Chart(fi).mark_circle(size=700).encode(x='총매출',y='판매량',color='상품')
elif sel == '매출원가' :
    chart = alt.Chart(fi).mark_circle(size=700).encode(x='총매출',y='매출원가',color='상품')
else :
    chart = alt.Chart(fi).mark_circle(size=700).encode(x='총매출',y='수익',color='상품')

fig = chart.properties(width=650, height=450)


st.altair_chart(fig, use_container_width=True)

st.subheader('2. Plotly Pie chart- 타이타닉 생존 분석')

titanic = pd.read_csv('https://raw.githubusercontent.com/huhshin/streamlit/master/data_titanic.csv')

if st.checkbox('타이타닉 데이터 조회'):
    st.dataframe(titanic)

tit = st.selectbox(
    '생존자 분석을 위한 항목을 선택하세요.',
    ('탑승지역별 분석', '객실등급별 분석') )
if tit == '탑승지역별 분석':
    sel = 'Embarked'
else:
    sel = 'Pclass'

# columns 함수를 이용하여 좌- pie 차트, 우- bar 차트
if tit == '탑승지역별 분석':
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(titanic, values = 'Survived', names = 'Embarked')
        fig.update_traces(textposition='inside', textinfo= 'percent+label+value')

if tit == '탑승지역별 분석' :
    col1,col2 = st.columns(2)
    with col1:
        # pie chart 그리기: values='Survived'
        fig = px.pie(titanic,values='Survived',names='Embarked')                # 탑승지역별 생존 분석 pie차트 생성
        fig.update_traces(textposition='inside',textinfo='percent+label+value') # text표시 추가
        fig.update_layout(font=dict(size=16))                                   # 폰트 사이즈 지정
        fig.update_layout(height=400, width=400)                                # 그래프 크기 조절
        fig.update(layout_showlegend=True)                                     # legened(범례)표시 조정
        st.plotly_chart(fig)                                                    # 차트 출력
    with col2:
        # bar chart 그리기: y="Survived", color="Sex"
        fig = px.bar(titanic,x ='Embarked',y='Survived',color='Sex')
        fig.update_layout(height=400, width=400)
        st.plotly_chart(fig)
else:        
    col3,col4 = st.columns(2)
    with col3:
        # pie chart 그리기: values='Survived'
        fig = px.pie(titanic,values='Survived',names='Pclass')
        fig.update_traces(textposition='inside',textinfo='percent+label+value')
        fig.update_layout(font=dict(size=16))
        fig.update_layout(height=400, width=400)
        fig.update(layout_showlegend=False)
        st.plotly_chart(fig)
    with col4:
        # bar chart 그리기: y="Survived", color="Sex"
        fig = px.bar(titanic,x ='Pclass',y='Survived',color='Sex')
        fig.update_layout(height=400, width=400)
        st.plotly_chart(fig)