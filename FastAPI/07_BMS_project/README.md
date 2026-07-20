# BMS 프로젝트

FastAPI, SQLAlchemy, Streamlit으로 구성한 책 관리 시스템입니다.

## 프로젝트 구조

```text
BMS_project/
├── fastapi_app/
│   ├── main.py          # FastAPI 앱 생성과 APIRouter 등록
│   ├── database.py      # Engine, SessionLocal, DeclarativeBase
│   ├── dependencies.py  # 요청별 DB Session 의존성
│   ├── models.py        # Book ORM 모델(Mapped, mapped_column)
│   ├── schemas.py       # Pydantic 요청·응답 스키마
│   ├── crud.py          # select(), Session.get() 기반 CRUD
│   └── routers/
│       └── books.py     # /books APIRouter 엔드포인트
└── streamlit_app.py     # 책 등록·목록·삭제 프론트엔드
```

## 설치

```bash
uv add fastapi "uvicorn[standard]" "sqlalchemy>=2.0,<3.0" pydantic streamlit requests
```

## 실행

### 1. FastAPI 백엔드

```bash
cd BMS_project/fastapi_app
uvicorn main:app --reload --port 8000
```

### 2. Streamlit 프론트엔드

새 터미널에서 실행합니다.

```bash
cd BMS_project
streamlit run streamlit_app.py
```

## 접속 주소

- Swagger UI: <http://127.0.0.1:8000/docs>
- Streamlit: <http://localhost:8501>

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/books/` | 전체 책 조회 |
| `GET` | `/books/{book_id}` | 단건 조회 |
| `POST` | `/books/` | 책 생성 (`201 Created`) |
| `DELETE` | `/books/{book_id}` | 책 삭제 |

## 데이터베이스

백엔드를 실행하면 `fastapi_app` 폴더에 `books.db` 파일이 자동으로 생성됩니다.
