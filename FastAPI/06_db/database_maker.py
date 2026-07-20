"""Database Maker

실행:
    uvicorn database_maker:app --reload --port 8005

"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)


# ═════════════════════════════════════════════════════════════════
# 1. DB 연결 설정
# ═════════════════════════════════════════════════════════════════
# SQLite는 파일 하나가 데이터베이스입니다.
# 상대 경로 ./fastapi_database.db는 명령을 실행한 작업 폴더를 기준으로 합니다.
DATABASE_URL = "sqlite:///./fastapi_database.db"

# engine은 DB 연결 통로입니다.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False},
    echo=False
)

# SessionLocal은 Session 객체를 만드는 팩토리입니다.
# autocommit=False이므로 데이터 변경 후 db.commit()을 직접 호출해야 합니다.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


# ═════════════════════════════════════════════════════════════════
# 2. ORM 모델 — Python 클래스 ↔ DB 테이블
# ═════════════════════════════════════════════════════════════════
class Base(DeclarativeBase):
    """모든 ORM 모델의 부모 클래스."""
    pass


class User(Base):
    """users 테이블과 매핑되는 ORM 클래스."""

    __tablename__ = "users"

    # Mapped[int]는 Python 타입과 DB 매핑 대상임을 함께 표현합니다.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # User 한 명은 Chatbot 대화 여러 개를 가질 수 있습니다(1:N).
    # delete-orphan: 사용자와 연결이 끊긴 대화 객체를 함께 삭제합니다.
    chatbot: Mapped[list[Chatbot]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

class Chatbot(Base):
    """chatbot 테이블과 매핑되는 대화 기록 ORM 클래스."""

    __tablename__ = "chatbot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)

    # DB 레벨 외래키 : chatbot.user -> users.id
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Python 객체 레벨 관계 : chat.user.name처럼 접근할 수 있음.
    user: Mapped[User] = relationship(back_populates="chatbot")


# 정의된 모델을 보고 실제 테이블을 생성
Base.metadata.create_all(bind=engine)



# ═════════════════════════════════════════════════════════════════
# 3. Pydantic 응답 스키마 — DB 모델과 HTTP 응답의 책임 분리
# ═════════════════════════════════════════════════════════════════
# SQLAlchemy의 DB 객체를 FastAPI 응답용 JSON으로 변환하기 위한 Pydantic 스키마
class UserResponse(BaseModel):
    # from_attributes=True :  SQLAlchemy 객체의 속성을 읽어 Pydantic으로 변환
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class ChatbotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_text: str
    output_text: str
    user_id: int

# ═════════════════════════════════════════════════════════════════
# 4. 요청별 DB 세션 의존성
# ═════════════════════════════════════════════════════════════════
def get_db() -> Generator[Session, None, None]:
    """요청마다 새 세션을 생성하고 종료 시 정리합니다."""
    
    db = SessionLocal()
    try:
        # yield 오른쪽의 Session이 Depends(get_db)를 통해 엔드포인트로 전달
        yield db
    except Exception:
        # commit 전에 오류가 생겼거나 commit이 실패하면 트랜잭션을 되돌림.
        db.rollback()
        raise
    finally:
        # 정상, 오류 여부와 관계없이 요청이 끝나면 연결 자원을 반납
        db.close()


app = FastAPI(
    title = "Database Maker",
    description="사용자 CRUD와 챗봇 대화 1:N 관계 실습"
)

# ═════════════════════════════════════════════════════════════════
# 5. 사용자 CRUD
# ═════════════════════════════════════════════════════════════════
@app.post('/users/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(name: str, email:str, db: Session=Depends(get_db)):
    """CREATE — 새 사용자를 등록합니다."""

    duplicate = db.scalar(select(User).where(User.email == email))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    
    user = User(name=name, email=email)
    db.add(user)            # 세션에 INSERT 대상으로 등록
    db.commit()             # 트랙잭션 확정 -> 실제 DB 반영
    db.refresh(user)        # DB가 생성한 id를 객체에 다시 읽기
    return user


@app.get('/users/', response_model=list[UserResponse])
def read_users(db: Session=Depends(get_db)):
    """READ — 전체 사용자를 id 순서로 조회합니다."""

    stmt = select(User).order_by(User.id)
    # scalars(stmt).all() : Result가 아닌 User 객체 리스트를 받음
    return db.scalars(stmt).all()


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """READ — 기본키로 사용자 한 명을 조회합니다."""

    # 기본키 조회는 select().where()보다 Session.get()이 간단합니다.
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    name: str,
    email: str,
    db: Session = Depends(get_db),
):
    """UPDATE — ORM 객체의 속성을 변경하고 commit합니다."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    duplicate = db.scalar(
        select(User).where(User.email == email, User.id != user_id)
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    user.name = name
    user.email = email
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """DELETE — 사용자를 삭제하고 연결된 대화도 함께 삭제합니다."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    db.delete(user)
    db.commit()


# ═════════════════════════════════════════════════════════════════
# 6. 챗봇 대화 저장·조회
# ═════════════════════════════════════════════════════════════════
@app.post(
    "/chatbot/{user_id}",
    response_model=ChatbotResponse,
    status_code=status.HTTP_201_CREATED,
)
def chatbot_conversation(
    input_text: str,
    user_id: int,
    db: Session = Depends(get_db),
):
    """사용자의 입력과 AI 답변을 chatbot 테이블에 저장합니다."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # OpenAI 연동해서 이 문자열 대신 모델 호출 결과를 저장.
    output_text = "안녕하세요. AI의 예시 답변입니다."

    chat = Chatbot(
        input_text = input_text,
        output_text = output_text,
        user_id= user_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat

@app.get("/chatbot/{user_id}", response_model=list[ChatbotResponse])
def read_chat_history(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자의 대화 기록을 등록 순서로 조회합니다."""

    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    stmt = select(Chatbot).where(Chatbot.user_id == user_id).order_by(Chatbot.id)
    return db.scalars(stmt).all()