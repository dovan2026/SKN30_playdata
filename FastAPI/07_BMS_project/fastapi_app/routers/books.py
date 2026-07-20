"""책과 관련된 엔드포인트를 모아둔 APIRouter."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
from dependencies import get_db
from schemas import BookCreate, BookResponse, BookUpdate


# prefix: 이 파일의 모든 URL 앞에 /books를 붙입니다.
# tags: Swagger UI에서 books 그룹으로 묶습니다.
router = APIRouter(prefix="/books", tags=["books"])

DbSession = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=list[BookResponse])
def read_books(db: DbSession):
    """전체 책 목록을 조회합니다."""
    return crud.get_books(db)

# 책 한권 조회!!


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

###################################################################
### 실습 : 제목, 저자 검색
###################################################################
@router.get("/search", response_model=list[BookResponse])
def search_books(
    db: DbSession,
    keyword: str = Query(
        min_length=1,
        description="검색할 책 제목 또는 저자",
    ),
):
    """제목 또는 저자에 검색어가 포함된 책을 조회합니다."""

    return crud.search_books(db, keyword)


@router.delete("/{book_id}")
def delete_book(book_id: int, db: DbSession):
    """책을 삭제합니다. 존재하지 않는 id는 404를 반환합니다."""
    if not crud.delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="책을 찾을 수 없습니다.")
    return {"message": "Deleted", "book_id": book_id}


###################################################################
### 실습 : 책 정보 수정
### PUT 엔드포인트 추가
###################################################################
@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book: BookUpdate,
    db: DbSession,
):
    """책 정보를 수정합니다."""

    updated_book = crud.update_book(
        db,
        book_id=book_id,
        title=book.title,
        author=book.author,
        publisher_year=book.publisher_year,
    )

    # 해당 ID의 책이 없으면 404 오류를 반환합니다.
    if updated_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="책을 찾을 수 없습니다.",
        )

    # 수정된 책은 BookResponse 형식으로 변환됩니다.
    return updated_book