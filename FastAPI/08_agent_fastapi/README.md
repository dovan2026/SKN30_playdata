# 블로그 콘텐츠 생성기


사용자가 입력한 주제를 기획자, 작가, 편집자, 번역가 역할의 네 노드가 순서대로
처리합니다. 각 단계의 결과는 그래프 상태에 저장되고, 마지막 한국어 콘텐츠와
중간 산출물을 JSON으로 반환합니다.

## 처리 흐름

```text
POST /langgraph
      │
      ▼
START → planner → writer → editor → translator → END
          │         │         │           │
          plan      draft     edited      final_content
```

LangGraph는 상태 스키마를 정의한 뒤 노드와 엣지를 연결하고 컴파일하는 방식으로
워크플로를 구성합니다. 자세한 개념은 [LangGraph 공식 문서](https://docs.langchain.com/oss/python/langgraph/graph-api)를 참고하세요.


## 파일 구성

| 파일 | 역할 |
| --- | --- |
| `main.py` | FastAPI 앱과 `POST /langgraph` 엔드포인트 |
| `graph.py` | 상태 정의, 네 노드와 순차 엣지 구성 |
| `agents.py` | ChatOpenAI 설정과 역할별 시스템 프롬프트 |
| `tasks.py` | 단계별 작업 프롬프트 생성 함수 |
| `index.html` | 주제 입력과 최종 결과 화면 |
| `script.js` | API 호출 및 화면 상태 처리 |
| `style.css` | 웹 화면 스타일 |
| `requirements.txt` | 파이썬 의존성 |

## 실행 환경

- Python 3.10 이상
- 유효한 OpenAI API 키
- 인터넷 연결

한 번의 요청에서 모델을 네 번 순차 호출하므로 API 비용이 발생하며 응답에 시간이
걸릴 수 있습니다.

## 설치 및 실행


### 1. 환경변수 설정


생성된 `.env` 파일을 열어 실제 키를 입력합니다.

```dotenv
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_MODEL`은 선택 사항이며 생략하면 `gpt-4.1-mini`를 사용합니다. `.env`는
비밀정보이므로 Git에 커밋하거나 공유하지 마세요.

### 2. FastAPI 서버 실행

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

또는 다음 명령을 사용할 수 있습니다.

```powershell
python main.py
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

### 3. 웹 UI 실행

백엔드를 켜 둔 상태에서 새 터미널을 열고 같은 폴더에서 실행합니다.

```powershell
python -m http.server 5500
```

브라우저에서 <http://127.0.0.1:5500>을 엽니다.

## API 사용법

### 요청

```http
POST /langgraph
Content-Type: application/json
```

```json
{
  "topic": "생성형 AI가 소프트웨어 개발에 미치는 영향"
}
```

PowerShell:

```powershell
$body = @{ topic = "생성형 AI가 소프트웨어 개발에 미치는 영향" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/langgraph" -Method Post -ContentType "application/json" -Body $body
```

### 응답 형태

```json
{
  "topic": "입력 주제",
  "plan": "기획 결과",
  "draft": "초안",
  "edited_content": "편집된 게시물",
  "final_content": "최종 한국어 콘텐츠"
}
```

웹 UI에는 `final_content`만 표시되며, 전체 중간 결과는 API 응답이나 Swagger
UI에서 확인할 수 있습니다.


## 문제 해결

### `ModuleNotFoundError`

가상환경이 활성화됐는지 확인한 뒤 의존성을 다시 설치합니다.

```powershell
python -m pip install -r requirements.txt
```

### OpenAI API 키 오류

현재 작업 폴더에 `.env`가 존재하고 `OPENAI_API_KEY`가 올바른지 확인한 후 서버를
다시 시작합니다.

### 모델 접근 오류

계정에서 `OPENAI_MODEL`에 지정한 모델을 사용할 수 있는지 확인하세요. 필요하면
`.env`에서 접근 가능한 모델명으로 변경한 후 서버를 다시 시작합니다.

### 웹 UI에서 `Failed to fetch`

- <http://127.0.0.1:8000/docs>가 열리는지 확인합니다.
- 백엔드가 `8000`번 포트에서 실행 중인지 확인합니다.
- HTML 파일을 직접 열지 말고 `python -m http.server 5500`으로 실행합니다.

