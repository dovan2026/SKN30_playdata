import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# --------------------------
# Streamlit 설정
# --------------------------

st.set_page_config(
    page_title="AI 미국주식 포트폴리오 플래너",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI 미국주식 포트폴리오 플래너")
st.markdown(
    """
    CrewAI 기반 멀티에이전트 투자 분석 시스템

    - 종목 분석 전문가
    - 헷지 전략 전문가
    - 증권가 컨설턴트 플래너

    가 협업하여 투자 보고서를 생성합니다.
    """
)

# --------------------------
# 입력 UI
# --------------------------

topic = st.text_input(
    "분석할 투자 주제를 입력하세요",
    placeholder="예: AI, 반도체, 양자컴퓨터, 클라우드, 로봇"
)

# --------------------------
# 실행 버튼
# --------------------------

if st.button("🚀 포트폴리오 분석 시작"):

    if not topic:
        st.warning("분석할 주제를 입력해주세요.")
        st.stop()

    with st.spinner("에이전트들이 리서치 중입니다..."):

        try:

            # --------------------------
            # Tool
            # --------------------------

            search_tool = SerperDevTool()

            scrape_tool = ScrapeWebsiteTool(
                website_url="https://www.sec.gov/"
            )

            # --------------------------
            # Manager Agent
            # --------------------------

            planner_agent = Agent(
                role="증권가 컨설턴트 플래너",
                goal=(
                    "최적 포트폴리오를 구성해주고 "
                    "그 이유를 명확하게 설명한다. "
                    "{topic}에 대한 종합적인 자산 운용 전략을 수립한다."
                ),
                backstory=(
                    "30년 경력의 베테랑 증권 컨설턴트로 "
                    "다양한 데이터를 활용하여 "
                    "최적의 포트폴리오를 설계한다."
                ),
                allow_delegation=True,
                llm="gpt-4o-mini",
                verbose=True
            )

            # --------------------------
            # 종목 분석 Agent
            # --------------------------

            ticker_agent = Agent(
                role="미국 주식 종목 분석 전문가",
                goal=(
                    "최신 트렌드와 SEC 자료를 분석하여 "
                    "{topic} 관련 유망 종목을 발굴한다."
                ),
                backstory=(
                    "미국 주식 리서치 전문가로 "
                    "기업 실적, SEC 공시, 산업 트렌드를 분석한다."
                ),
                tools=[
                    search_tool,
                    scrape_tool
                ],
                llm="gpt-4o-mini",
                verbose=True
            )

            # --------------------------
            # Hedge Agent
            # --------------------------

            hedge_agent = Agent(
                role="베테랑 헷지 종목 분석 전문가",
                goal=(
                    "{topic} 투자에 대한 리스크를 분석하고 "
                    "손실 방어 전략을 수립한다."
                ),
                backstory=(
                    "ETF, 채권, 금, 변동성 상품 등 "
                    "모든 헷지 자산에 정통한 전문가."
                ),
                tools=[
                    search_tool
                ],
                llm="gpt-4o-mini",
                verbose=True
            )

            # --------------------------
            # Task
            # --------------------------

            planner_task = Task(
                description=(
                    "{topic}에 대한 종합적인 투자 포트폴리오를 구성하세요.\n\n"
                    "반드시 아래 내용을 포함하세요.\n\n"
                    "1. 산업 전망\n"
                    "2. 추천 미국 주식 TOP5\n"
                    "3. 종목별 투자 이유\n"
                    "4. 예상 성장 모멘텀\n"
                    "5. 주요 리스크\n"
                    "6. 헷지 전략\n"
                    "7. 추천 자산 배분\n"
                    "8. 결론\n"
                ),
                expected_output=(
                    "{topic} 기반의 투자 포트폴리오와 "
                    "헷지 전략이 포함된 종합 자산 운용 보고서"
                )
            )

            # --------------------------
            # Crew
            # --------------------------

            crew = Crew(
                agents=[
                    ticker_agent,
                    hedge_agent
                ],
                tasks=[
                    planner_task
                ],
                process=Process.hierarchical,
                manager_agent=planner_agent,
                verbose=True
            )

            result = crew.kickoff(
                inputs={
                    "topic": topic
                }
            )

            # --------------------------
            # 출력
            # --------------------------

            st.success("분석 완료!")

            st.markdown("---")

            st.subheader("📗 최종 투자 보고서")

            st.markdown(str(result))

            st.download_button(
                label="📥 보고서 다운로드",
                data=str(result),
                file_name=f"{topic}_investment_report.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

# from dotenv import load_dotenv
# import os
# from crewai_tools import SerperDevTool, ScrapeWebsiteTool
# from crewai import Agent, Task, Crew, Process

# load_dotenv()

# # 도구 인스턴스 생성
# search_tool = SerperDevTool()
# scrape_tool = ScrapeWebsiteTool(website_url='https://www.sec.gov/')

# # 총괄 자산 플래너(관리자 Agent)
# planner_agent = Agent(
#     role="증권가 컨설턴트 플래너",
#     goal="최적 포트폴리오를 구성해주고 그에 대한 이유를 명확하게 답변한다. {topic}을 input 받으면 그 {topic}과 관련하여 종합적인 플래너를 설계해준다.",
#     backstory="30년 경력의 베테랑 증권 컨설턴트로 다양한 데이터를 기반으로 소비자를 만족시켜준다.",
#     allow_delegation=True,       # 다른 에이전트에게 업무 위임을 허용
#     llm='gpt-4o-mini',
#     verbose=True
# )

# # 종목 분석 전문가 Agent(공격 종목 추천 담당)
# ticker_agent = Agent(
#     role="미국 주식 종목 분석 전문가",
#     goal="최신 트렌드와 sec.gov 사이트를 조사하여 근거 있는 종목 리서치 보고서를 만든다. {topic}을 input 받으면 {topic}에 대한 전망 및 추세 등 자세한 리서치 보고서를 제공한다.",
#     backstory="베테랑 컨설턴트와 같이 일한 경력자로 미국 주식에 대한 모든 것을 알고 있다.",
#     tools=[search_tool, scrape_tool],  # scrape_tool 추가
#     llm='gpt-4o-mini',
#     verbose=True
# )

# # 헷지 전문가 Agent(헷지 종목 추천 담당)
# hedge_agent = Agent(
#     role="베테랑 헷지 종목 분석 전문가",
#     goal="공격적인 미국 주식 종목과는 별개로 자산 헷지를 위한 것만을 목표로 한다. {topic}과 관련하여 헷지를 통한 방어책을 제시한다. 자세한 헷지 전략을 통해서 {topic} 투자에 의한 손실을 최대한 방어한다.",
#     backstory="미국 주식에서의 모든 헷지 종목을 알고 있고 미국 주식을 소비하는 모든 사람들에게 만족감 100%를 준다.",
#     tools=[search_tool],
#     llm='gpt-4o-mini',
#     verbose=True
# )

# # Task 정의 (총괄 플래너가 하위 에이전트에게 지시할 전체 목표)
# planner_task = Task(
#     description=(
#         "{topic}에 대한 종합적인 투자 포트폴리오를 구성하세요. "
#         "미국 주식 종목 분석 전문가의 리서치 결과와, 헷지 전문가의 방어 전략을 모두 취합하여 "
#         "명확한 근거가 포함된 자산 운용 계획서를 한국어로 작성해주세요."
#     ),
#     expected_output=(
#         "{topic} 기반의 추천 종목, 투자 전망, 그리고 손실 방어를 위한 헷지 전략이 모두 포함된 종합 자산 플랜 보고서"
#     )
#     # Process.hierarchical에서는 Task에 agent를 직접 명시하지 않음
# )

# # Crew 구성 (계층적 프로세스 사용)
# crew = Crew(
#     agents=[ticker_agent, hedge_agent],  # 하위 실행에 참여할 에이전트들(관리자 제외)
#     tasks=[planner_task],
#     process=Process.hierarchical,       
#     manager_agent=planner_agent,        # 총괄 자산 플래너를 매니저로 지정
#     verbose=True
# )

# x = input("분석할 주제(topic)를 입력하세요: ")

# # kickoff 실행 시 inputs 딕셔너리로 변수 전달
# result = crew.kickoff(inputs={'topic': x})

# print("\n\n📗 최종 자산 계획서:\n")
# print(result)