"""책과 관련된 엔드포인트를 모아둔 APIRouter."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud
from dependencies import get_db
from schemas import BookCreate, BookResponse


# prefix: 이 파일의 모든 URL 앞에 /books를 붙입니다.
# tags: Swagger UI에서 books 그룹으로 묶습니다.
router = APIRouter(prefix='/books', tags=['books'])
Dbsession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[BookResponse])
def read_books(db: DbSession):
    """전체 책 목록을 조회합니다."""
    return crud.get_books(db)

@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_book(book: BookCreate, db: DbSession):
    """새 책을 등록합니다."""
    return crud.create_book(
        db,
        title=book.title,
        author=book.author,
        publisher_year=book.publisher_year
    )

@router.delete("/{book_id}")
def delete_book(book_id: int, db: DbSession):
    """책을 삭제합니다. 존재하지 않는 id는 404를 반환합니다."""
   if not crud.delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    return {'message': 'Deleted', 'book_id': book_id}
