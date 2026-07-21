# 전체 아키텍처

이 문서는 Slack 경제 뉴스 챗봇의 런타임 구성, 요청 처리 순서, LangGraph 워크플로, 코드 계층, SQLite 저장 구조와 테스트 구조를 설명합니다.

## 1. 전체 런타임 아키텍처

```mermaid
flowchart LR
    USER["Slack 사용자"]
    SWAGGER["Swagger / REST 사용자"]
    CLI["CLI 스크립트"]
    SLACK["Slack 플랫폼"]
    TUNNEL["Cloudflare Tunnel"]

    subgraph FASTAPI["FastAPI 애플리케이션"]
        HEALTH["GET /health/live<br/>GET /health/ready"]
        SLACK_API["POST /slack/events"]
        AGENT_API["POST /agent/run"]
        BOLT["Slack Bolt Handler<br/>서명 검증 및 ACK"]
        MAIN["app/main.py<br/>전체 객체 조립"]
    end

    subgraph SERVICES["서비스 계층"]
        SH["SlackHandlers<br/>명령·이벤트 처리"]
        QUEUE[("asyncio.Queue")]
        WORKER["JobService Worker"]
        AGENT_SERVICE["AgentService<br/>공통 Agent 실행"]
        REPOSITORY["RunRepository"]
    end

    subgraph LANGGRAPH["LangGraph Agent"]
        GRAPH["StateGraph"]
        PLAN["질문 계획"]
        SEARCH["뉴스 검색"]
        ANALYZE["경제 분석"]
        FORMAT["Slack 답변 생성"]
        ERROR["오류 처리"]
    end

    subgraph EXTERNAL["외부 서비스"]
        TAVILY["Tavily Search API"]
        OPENAI["OpenAI API"]
        SLACK_WEB["Slack Web API"]
    end

    subgraph STORAGE["SQLite 저장소"]
        RUN_DB[("runs.sqlite<br/>실행 기록")]
        CHECKPOINT_DB[("checkpoints.sqlite<br/>대화 상태")]
    end

    USER -->|"/econ 질문"| SLACK
    USER -->|"스레드 후속 질문"| SLACK
    SLACK -->|"서명된 HTTP POST"| TUNNEL
    TUNNEL --> SLACK_API
    SLACK_API --> BOLT
    BOLT --> SH

    SH -->|"즉시 ACK"| SLACK
    SH -->|"진행 메시지"| SLACK_WEB
    SH -->|"AgentJob 등록"| QUEUE
    QUEUE --> WORKER
    WORKER --> AGENT_SERVICE

    SWAGGER --> AGENT_API
    AGENT_API --> AGENT_SERVICE
    CLI --> AGENT_SERVICE

    AGENT_SERVICE --> GRAPH
    GRAPH --> PLAN
    PLAN --> SEARCH
    SEARCH --> TAVILY
    SEARCH --> ANALYZE
    ANALYZE --> OPENAI
    ANALYZE --> FORMAT
    PLAN -. 오류 .-> ERROR
    SEARCH -. 오류 .-> ERROR
    ANALYZE -. 오류 .-> ERROR

    AGENT_SERVICE --> REPOSITORY
    REPOSITORY --> RUN_DB
    GRAPH <--> CHECKPOINT_DB

    FORMAT --> WORKER
    ERROR --> WORKER
    WORKER -->|"최종 답변 또는 오류"| SLACK_WEB
    SLACK_WEB --> SLACK
    SLACK --> USER

    MAIN -. 구성 .-> BOLT
    MAIN -. 구성 .-> AGENT_SERVICE
    MAIN -. 구성 .-> GRAPH
    MAIN -. 구성 .-> REPOSITORY
```

## 2. Slack 질문 처리 순서

```mermaid
sequenceDiagram
    autonumber

    actor User as Slack 사용자
    participant Slack as Slack 플랫폼
    participant Tunnel as Cloudflare Tunnel
    participant API as FastAPI /slack/events
    participant Handler as SlackHandlers
    participant Queue as asyncio.Queue
    participant Worker as JobService
    participant Agent as AgentService
    participant Graph as LangGraph
    participant Search as Tavily
    participant LLM as OpenAI
    participant Runs as runs.sqlite
    participant CP as checkpoints.sqlite

    User->>Slack: /econ 반도체 수출
    Slack->>Tunnel: Slash Command HTTP POST
    Tunnel->>API: POST /slack/events
    API->>Handler: Bolt 서명 검증 후 전달

    Handler-->>Slack: 즉시 ACK
    Handler->>Slack: 분석 진행 메시지 게시
    Slack-->>Handler: progress message ts

    Handler->>Runs: status=queued 저장
    Handler->>Queue: AgentJob 등록
    Queue->>Worker: 작업 전달

    Worker->>Agent: 질문 실행
    Agent->>Runs: status=running
    Agent->>Graph: ainvoke(thread_id)

    Graph->>CP: 기존 스레드 상태 조회
    Graph->>Search: 뉴스 검색
    Search-->>Graph: 뉴스와 출처
    Graph->>LLM: 구조화 경제 분석 요청
    LLM-->>Graph: EconomicAnalysis
    Graph->>CP: 최신 그래프 상태 저장
    Graph-->>Agent: 최종 답변

    Agent->>Runs: status=success, answer 저장
    Agent-->>Worker: AgentResponse
    Worker->>Slack: thread_ts에 최종 답변 게시
    Slack-->>User: 분석 결과 표시
```

## 3. LangGraph 내부 워크플로

```mermaid
flowchart TD
    START(("START"))
    PLAN["plan_query<br/>검색 계획 수립"]
    DECISION{"뉴스 검색이<br/>필요한가?"}
    SEARCH["search_news<br/>Tavily 뉴스 검색"]
    ANALYZE["analyze_economy<br/>OpenAI 구조화 분석"]
    FORMAT["format_answer<br/>Slack 형식 답변"]
    ERROR["handle_error<br/>오류 코드와 원인 정리"]
    END(("END"))

    START --> PLAN
    PLAN --> DECISION

    DECISION -->|"첫 질문·새 주제·최신 정보"| SEARCH
    DECISION -->|"기존 출처 재사용 가능"| ANALYZE

    SEARCH -->|"NewsItem + Source"| ANALYZE
    ANALYZE --> FORMAT
    FORMAT --> END

    PLAN -. "계획 실패" .-> ERROR
    SEARCH -. "검색 실패·빈 결과" .-> ERROR
    ANALYZE -. "분석 실패" .-> ERROR
    ERROR --> END
```

LangGraph가 공유하는 상태는 다음과 같습니다.

```text
AgentState
├─ query
├─ run_id
├─ messages
├─ plan
├─ search_results
├─ analysis
├─ sources
├─ final_answer
└─ error
```

## 4. 코드 계층 구조

```mermaid
flowchart TD
    ENTRY["진입점<br/>app/main.py"]

    API["API 계층<br/>app/api"]
    SLACK_APP["Slack 어댑터<br/>app/slack_app.py"]
    SERVICE["서비스 계층<br/>app/services"]
    AGENT["Agent 계층<br/>app/agent"]
    TOOL["도구 계층<br/>app/tools"]
    DB["DB 계층<br/>app/db"]
    SCHEMA["데이터 계약<br/>app/schemas"]
    CORE["공통 설정<br/>app/core"]

    ENTRY --> API
    ENTRY --> SLACK_APP
    ENTRY --> SERVICE
    ENTRY --> AGENT
    ENTRY --> TOOL
    ENTRY --> DB
    ENTRY --> CORE

    API --> SERVICE
    SLACK_APP --> SERVICE
    SERVICE --> AGENT
    SERVICE --> DB
    AGENT --> TOOL

    API -. 사용 .-> SCHEMA
    SERVICE -. 사용 .-> SCHEMA
    AGENT -. 사용 .-> SCHEMA
    TOOL -. 사용 .-> SCHEMA
```

각 계층의 책임은 다음과 같습니다.

| 계층 | 주요 파일 | 책임 |
|---|---|---|
| 진입점 | `app/main.py` | 모든 객체 생성과 연결 |
| API | `app/api/*.py` | HTTP 요청과 응답 |
| Slack | `app/slack_app.py` | Slash Command 및 이벤트 등록 |
| 서비스 | `app/services/*.py` | 업무 흐름, 작업 큐, Agent 실행 |
| Agent | `app/agent/*.py` | LangGraph와 OpenAI 분석 |
| 도구 | `app/tools/*.py` | Tavily 뉴스 검색 |
| DB | `app/db/*.py` | 실행 기록 저장 및 조회 |
| 스키마 | `app/schemas/*.py` | 계층 간 데이터 형식 |
| 설정 | `app/core/*.py` | 환경변수와 로깅 |

## 5. SQLite 저장 구조

```mermaid
flowchart LR
    QUESTION["사용자 질문"]
    RUN["한 번의 Agent 실행"]
    THREAD["동일한 대화 스레드"]

    subgraph RUNS["runs.sqlite"]
        RECORD1["실행 기록 1<br/>run_id=A<br/>thread_id=X"]
        RECORD2["실행 기록 2<br/>run_id=B<br/>thread_id=X"]
        RECORD3["실행 기록 3<br/>run_id=C<br/>thread_id=Y"]
    end

    subgraph CHECKPOINT["checkpoints.sqlite"]
        STATE_X["thread_id=X<br/>대화·뉴스·분석 상태"]
        STATE_Y["thread_id=Y<br/>별도 대화 상태"]
    end

    QUESTION --> RUN
    RUN --> RECORD1
    THREAD --> RECORD2

    RECORD1 --> STATE_X
    RECORD2 --> STATE_X
    RECORD3 --> STATE_Y
```

핵심 차이는 다음과 같습니다.

```text
run_id
= 질문 실행 한 번마다 새로운 값

thread_id
= 같은 대화를 이어갈 때 동일한 값
```

- `runs.sqlite`: 질문별 실행 이력
- `checkpoints.sqlite`: 스레드별 LangGraph 대화 상태

## 6. 핵심 요약

```text
외부 요청 계층
Slack / REST / CLI
        ↓
서비스 계층
SlackHandlers / JobService / AgentService
        ↓
Agent 계층
LangGraph
        ↓
외부 도구
Tavily / OpenAI
        ↓
저장 계층
runs.sqlite / checkpoints.sqlite
        ↓
응답 계층
Slack 스레드 / REST 응답 / CLI 출력
```

이 구조의 중심은 `AgentService`입니다. Slack, FastAPI, CLI가 서로 다른 방식으로 질문을 받더라도 모두 동일한 `AgentService → LangGraph` 실행 경로를 사용합니다.

