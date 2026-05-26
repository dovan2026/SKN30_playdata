import streamlit as st
import pandas as pd
import numpy as np

st.title('Data Display elements')
st.caption('text 참고사이트: https://docs.streamlit.io/library/api-reference/data')

# 1.Metric (단일 지표 카드)

st.header('1.Metric')
# label = 지표 이름 / valeu : 값 / delta : 변화량
st.metric(label = "Temperature", value = "70", delta = "1.2")

# 2.여러 개의 metric 카드 (한줄)
col1, col2, col3 = st.columns(3)
col1.metric("Temperature", "70", "1.2")
col2.metric("wind", "9 mph", "-8%")
col3.metric("Humidity", "86%", "-6%")

# 4. Grid 형태의 metric 카드
a, b = st.columns(2)
c, d = st.columns(2)

st.header('Dataframe 조회하기')
titanic = pd.read_csv('data/t2.csv')
st.dataframe(titanic.head(10))  # 인터랙티브 테이블 (스크롤, 정렬 가능)

# pandas styler 활용
# 난수 데이터프레임 생성(10행 & 20행)
df = pd.DataFrame(np.random.randn(10,20), columns = ("col %d" % i for i in range(20)))

# 각 열의 최대값을 강조 표시
st.dataframe(df.style.highlight_max(axis=0))

from numpy.random import default_rng as rng
df = pd.DataFrame(
    {
        "name": ["Roadmap", "Extras", "Issues"],
        "url": [
            "https://roadmap.streamlit.app/",
            "https://extras.streamlit.app/",
            "https://issues.streamlit.app/",
        ],
        "stars": rng(0).integers(0, 1000, size=3),
        "views_history": rng(0).integers(0, 5000, size=(3, 30)).tolist(),
    }
)

st.dataframe(
    df,
    column_config={
        "name": "App name",
        "stars": st.column_config.NumberColumn(
            "Github Stars",
            help="Number of stars on GitHub",
            format="%d ⭐",
        ),
        "url": st.column_config.LinkColumn("App URL"),
        "views_history": st.column_config.LineChartColumn(
            "Views (past 30 days)", y_min=0, y_max=5000
        ),
    },
    hide_index=True,
)