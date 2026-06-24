import streamlit as st
from dotenv import load_dotenv
import asyncio
import nest_asyncio

load_dotenv()
nest_asyncio.apply()

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="AI 여행 플래너",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Full_AI 여행 플래너")
st.title("✈️ CrewAI 여행 플래너")
st.write("여행 전문가와 요리 전문가가 협업하여 여행 계획을 만들어줍니다.")

region = st.text_input(
    "여행 지역",
    value="서울 근교"
)

days = st.selectbox(
    "여행 기간",
    ["1박 2일", "2박 3일", "3박 4일"]
)

if st.button("여행 계획 생성"):

    with st.spinner("AI 에이전트들이 여행 계획을 작성 중입니다..."):

        try:

            # -----------------------------
            # Tool
            # -----------------------------
            search_tool = SerperDevTool()

            # -----------------------------
            # Manager Agent
            # -----------------------------
            planner_agent = Agent(
                role="총괄 여행 플래너",
                goal=(
                    f"{region} 여행에 대한 최종 여행 계획서를 작성하고 "
                    "하위 에이전트들의 결과를 종합한다."
                ),
                backstory=(
                    "10년 경력의 여행 컨설턴트로 "
                    "다양한 전문가 의견을 취합하여 "
                    "최적의 여행 일정을 제안한다."
                ),
                allow_delegation=True,
                verbose=True,
                llm="gpt-5.4-mini"
                llm="gpt-4o-mini"
            )

            # -----------------------------
            # Travel Agent
            # -----------------------------
            travel_agent = Agent(
                role="여행 전문가",
                goal=(
                    f"{region}의 최신 여행 트렌드를 조사하고 "
                    "관광 명소 및 일정을 추천한다."
                ),
                backstory=(
                    "국내 여행 전문 컨설턴트로 "
                    "최신 관광 트렌드와 SNS 인기 장소에 밝다."
                ),
                tools=[search_tool],
                verbose=True,
                llm="gpt-5.4-mini"
                llm="gpt-4o-mini"
            )

            # -----------------------------
            # Culinary Agent
            # -----------------------------
            culinary_agent = Agent(
                role="요리 전문가",
                goal=(
                    "추천된 여행지와 잘 어울리는 "
                    "현지 음식 및 맛집 정보를 추천한다."
                ),
                backstory=(
                    "국내 음식 문화 전문가로 "
                    "지역 특산물과 대표 음식을 잘 알고 있다."
                ),
                tools=[search_tool],
                verbose=True,
                llm="gpt-5.4-mini"
                llm="gpt-4o-mini"
            )

            # -----------------------------
            # Task
            # -----------------------------
            planner_task = Task(
                description=f"""
                최신 여행 트렌드를 반영하여
                {region} {days} 여행 계획을 작성하라.

                반드시 포함:
                1. 시간대별 여행 일정
                2. 추천 관광지
                3. 추천 음식
                4. 맛집 추천
                5. 예상 비용
                6. 여행 팁

                최종 결과는 한국어로 작성하라.
                """,
                expected_output="""
                여행 일정표,
                음식 추천,
                예상 비용,
                여행 팁이 포함된
                완성형 여행 계획서
                """
            )

            # -----------------------------
            # Crew
            # -----------------------------
            crew = Crew(
                agents=[
                    travel_agent,
                    culinary_agent
                ],
                tasks=[
                    planner_task
                ],
                process=Process.hierarchical,
                manager_agent=planner_agent,
                verbose=True
            )

            result = crew.kickoff()
            # Streamlit의 이벤트 루프와 충돌을 피하기 위해
            # kickoff_async를 사용하고 asyncio.run으로 실행합니다.
            # nest_asyncio.apply()가 호출되었기 때문에 가능합니다.
            result = asyncio.run(crew.kickoff_async())

            st.success("여행 계획 생성 완료!")

            st.markdown("---")
            st.subheader("📗 최종 여행 계획서")

            st.markdown(str(result))

        except Exception as e:
            st.error(f"오류 발생: {e}")