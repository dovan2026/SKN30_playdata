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


###################################################################
### 실습 : 책 정보 수정
###################################################################
def update_book(
    db: Session,
    book_id: int,
    title: str,
    author: str,
    publisher_year: str,
) -> models.Book | None:
    """UPDATE: 책이 있으면 정보를 수정하고, 없으면 None을 반환합니다."""

    # 기존 get_book() 함수를 이용하여 수정할 책을 조회합니다.
    book = get_book(db, book_id)

    # 해당 ID의 책이 없으면 None을 반환합니다.
    if book is None:
        return None

    # SQLAlchemy 객체의 속성을 새로운 값으로 변경합니다.
    book.title = title
    book.author = author
    book.publisher_year = publisher_year

    # 변경 내용을 데이터베이스에 반영합니다.
    db.commit()

    # 데이터베이스의 최신 값을 객체에 다시 불러옵니다.
    db.refresh(book)

    # 수정된 Book 객체를 반환합니다.
    return book

###################################################################
### 실습 : 제목, 저자 검색
###################################################################
def search_books(
    db: Session,
    keyword: str,
) -> list[models.Book]:
    """SEARCH: 제목 또는 저자에 검색어가 포함된 책을 조회합니다."""

    stmt = (
        select(models.Book)
        .where(
            models.Book.title.ilike(f"%{keyword}%")
            | models.Book.author.ilike(f"%{keyword}%")
        )
        .order_by(models.Book.id)
    )

    return list(db.scalars(stmt).all())