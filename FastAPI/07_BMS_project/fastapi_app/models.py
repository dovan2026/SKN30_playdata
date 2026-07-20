"""책 관리 시스템의 SQLAlchemy ORM 모델."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Book(Base):
    """Book 객체 하나가 books 테이블의 행 하나에 대응합니다."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    publisher_year: Mapped[str] = mapped_column(String(10), nullable=False)

    def __repr__(self) -> str:
        return (
            f"Book(id={self.id}, title={self.title!r}, "
            f"author={self.author!r}, publisher_year={self.publisher_year!r})"
        )