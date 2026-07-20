"""SQLite 연결, SQLAlchemy, 세션 팩토리 설정."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 현재 터미널의 작업 폴더에 books.db 파일이 생성.
SQLALCHEMY_DATABASE_URL = "sqlite:///./books.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite의 동일 스레드 제한 해제
    echo=False          # True로 바꾸면 실제 SQL을 터미널에서 확인 가능
)

# 호출할 때마다 독립적인 Session을 만드는 세션 팩토리
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """모든 ORM 모델이 상속하는 SQLAlchemy 클래스."""
