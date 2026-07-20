"""Book 모델의 DB 접근을 담당하는 SQLAlchemy CRUD 모듈."""

from sqlalchemy import select
from sqlalchemy.orm import Session

import models


def create_book(
    db: Session,
    title: str,
    author: str,
    publisher_year: str,
) -> models.Book:
    """CREATE: 새 책을 저장하고 DB가 만든 id를 포함한 객체를 반환합니다."""
    book = models.Book(
        title=title,
        author=author,
        publisher_year=publisher_year
    )
    db.add(book)        # 생성한 book 객체를 현재 세션에 추가
    db.commit()         # 트랜잭션을 확정하여 실제 DB에 반영
    db.refresh(book)
    return book


def get_books(db: Session) -> list[models.Book]:
    """READ: 전체 책을 id 순서로 조회합니다."""
    # SELECT * FROM books IRDER BY id
    stmt = select(models.Book).order_by(models.Book.id)
    return list(db.scalars(stmt).all())


def get_book(db: Session, book_id: int) -> models.Book | None:
    """READ: 기본키로 책 한 권을 조회합니다."""
    # 기본키가 book_id인 Book 객체를 조회
    return db.get(models.Book, book_id)


def delete_book(db: Session, book_id: int) -> bool:
    """DELETE: 책이 있으면 삭제하고 True, 없으면 False를 반환합니다."""

    # 기본키 사용하여 삭제할 책 조회
    # book = db.get(models.Book, book_id)
    book = get_book(db, book_id)

    # 해당 id의 책이 존재하지 않으면 삭제하지 않고 False를 반환
    if book is None:
        return False

    # 조회한 Book 객체를 삭제 대상으로 등록
    db.delete(book)

    # 트랜잭션을 확정하여 DB에 반영
    db.commit()
   
    return True