# 경제 뉴스 분석 에이전트 Slack 챗봇

Tavily 뉴스 검색 결과를 LangGraph와 OpenAI로 분석하고, FastAPI 또는 Slack `/econ` 명령으로 답변을 제공하는 챗봇입니다.

## 구성

```text
Slack /econ
  -> FastAPI + Slack Bolt
  -> asyncio.Queue worker
  -> AgentService
  -> LangGraph (plan -> conditional search -> analyze -> format)
  -> Tavily + OpenAI
  -> SQLite checkpoints / agent_runs
  -> Slack thread
```

첫 질문은 최근 7일 뉴스를 검색합니다. 같은 Slack 스레드의 후속 질문은 새 주제나 최신 자료가 필요할 때만 다시 검색합니다. 검색 근거가 없으면 LLM의 일반 지식으로 대체하지 않고 오류를 반환합니다.

## 1. 설치

Python 3.12와 `uv`가 필요합니다.

```powershell
uv python install 3.12
uv sync --all-groups
Copy-Item .env.sample .env
```

`.env`에 다음 값을 설정합니다.

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-terra
TAVILY_API_KEY=...

SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
```

`.env`와 SQLite 파일은 Git에서 제외됩니다.

## 2. 단계별 실행

뉴스 검색만 확인합니다.

```powershell
uv run python scripts/search_news.py "반도체 수출"
```

LangGraph 터미널 MVP를 실행합니다.

```powershell
uv run python scripts/run_agent.py "반도체 수출"
```

같은 대화를 이어가려면 첫 실행에 표시된 ID를 사용합니다.

```powershell
uv run python scripts/run_agent.py "환율 영향만 자세히 설명해줘" --thread-id "이전-thread-id"
```

FastAPI를 실행합니다.

```powershell
uv run uvicorn app.main:app --reload
```

- Swagger: `http://localhost:8000/docs`
- Liveness: `GET /health/live`
- Readiness: `GET /health/ready`
- Agent: `POST /agent/run`


## 3. Slack App 설정

Slack App에서 다음을 설정합니다.

1. Bot Token Scopes: `commands`, `chat:write`, `channels:history`
2. Slash Command: `/econ`
3. Event Subscription: `message.channels`
4. 앱을 공개 채널에 초대하고 Workspace에 재설치
5. Bot Token과 Signing Secret을 `.env`에 저장

로컬 서버를 실행한 후 Cloudflare 임시 터널을 엽니다.

```powershell
cloudflared tunnel --url http://localhost:8000
```

Slack의 Slash Command 및 Event Subscription Request URL을 다음으로 설정합니다.

```text
https://<생성된-주소>/slack/events
```

`/econ 반도체 수출`을 입력하면 봇이 즉시 진행 메시지를 게시하고 최종 분석을 해당 메시지의 스레드에 작성합니다. 그 스레드에 일반 메시지로 후속 질문을 보내면 같은 LangGraph `thread_id`를 재사용합니다.

## 4. 저장과 장애 동작

- `data/checkpoints.sqlite`: LangGraph 스레드 체크포인트
- `data/runs.sqlite`: `agent_runs` 실행 기록
- 프로세스 시작 시 남아 있는 `queued`/`running` 기록은 `interrupted`로 변경됩니다.
- 프로세스 내 큐는 재시작 시 복원되지 않습니다. Redis/PostgreSQL 워커 전환은 운영 배포 단계의 후속 범위입니다.
- Tavily 또는 OpenAI 실패 시 실행 ID와 오류 코드를 남기고 근거 없는 분석을 만들지 않습니다.
