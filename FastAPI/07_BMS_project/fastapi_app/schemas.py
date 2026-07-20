"""책 API의 Pydantic 요청·응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field


class BookCreate(BaseModel):
    """POST /books/ 요청 본문 스키마."""

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    publisher_year: str = Field(min_length=1, max_length=10)

###################################################################
### 실습 : 책 정보 수정
###################################################################
class BookUpdate(BaseModel):
    """PUT /books/{book_id} 요청 본문 스키마."""

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    publisher_year: str = Field(min_length=1, max_length=10)


class BookResponse(BaseModel):
    """SQLAlchemy Book 객체를 JSON으로 변환하는 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    publisher_year:str