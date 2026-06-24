from dotenv import load_dotenv
import os

load_dotenv()

from crewai_tools import SerperDevTool

# 도구 인스턴스 생성
search_tool = SerperDevTool()

from crewai import Agent, Task, Crew, Process

# 총괄 여행 플래너(관리자 Agent)
planner_agent = Agent(
    role="총괄 여행 플래너",
    goal="최적의 서울 근교 1박 2일 여행 일정과 추천 음식을 종합하여 최종 여행 계획서를 작성",
    backstory="10년 경력의 베테랑 여행 컨설턴트로 다양한 분야의 의견을 취합하여 여행 계획을 완성",
    allow_delegation=True,       # 다른 에이전트에게 업무 위임을 허용
    llm='gpt-5.4-mini',
    verbose=True
)

# 여행 전문가 Agent(여행 일정 추천 담당)
travel_agent = Agent(
    role="여행 전문가",
    goal="최신 여행 트렌드를 조사하여 서울 근교의 인기 있는 여행지와 일정을 제안",
    backstory="국내 여행지에 대해 잘 알고 있는 전문가로, 최근 여행 트렌드를 바탕으로 관광지 추천",
    tools=[search_tool],
    llm='gpt-5.4-mini',
    verbose=True
)

# 요리 전문가 Agent(음식 추천 담당)
culinary_agent = Agent(
    role="요리 전문가",
    goal="추천된 여행지와 잘 어울리는 현지 음식 및 레시피 추천",
    backstory="국내 각 지역의 음식 문화와 레시피에 능통한 전문가로, 여행지에 어울리는 음식을 추천",
    tools=[search_tool],
    llm='gpt-5.4-mini',
    verbose=True
)

# Task 정의 (총괄 플래너에게 최종 여행 계획서 작성 지시)
planner_task = Task(
    description=(
        "국내 최신 여행 트렌드가 반영된 서울 근교의 1박 2일 여행 일정을 작성하고,"
        "각 여행지와 잘 어울리는 현지 음식과 레시피를 포함하여 여행 계획서를 한국어로 작성해주세요."
    ),
    expected_output=(
        "최신 여행 트렌드를 반영한 서울 근교 1박 2일 여행 일정과"
        "각 여행지의 현지 음식 및 간단한 레시피를 포함한 한국어 여행 계획서"
    ),
    # agent=planner_agent
)

# Crew 구성 (계층적 프로세스 사용)
# 매니저 설정이 제일 중요.
crew = Crew(
    agents=[travel_agent, culinary_agent],  # 하위 실행에 참여할 에이전트들(관리자 제외)
    tasks=[planner_task],
    process=Process.hierarchical,       # 매니저한테 goal을 디테일하게 작성해야 됨.
    manager_agent=planner_agent,        # 총괄 여행 플래너를 매니저로 지정.
    verbose=True
)

result = crew.kickoff()
print("\n\n📗 최종 여행 계획서:\n")
print(result)