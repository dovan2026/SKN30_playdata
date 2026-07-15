"""05_post_pydantic — POST 요청 + Pydantic 데이터 검증.

학습 목적:
    1) Pydantic BaseModel 로 요청·응답 형태 정의
    2) Field(ge=1) 같은 검증 규칙 — 어기면 422 자동 응답
    3) response_model 로 응답 형태 자동 변환·문서화
    4) HTTPException 으로 의도적 4xx 응답 (404, 409 등)

실행:
    uvicorn main:app --reload

Swagger UI 에서 POST 테스트:
    http://127.0.0.1:8000/docs
    → POST /songs 펼치기 → Try it out → JSON 입력 → Execute

검증 실패 케이스 (rank=0 → 422):
    curl -X POST http://127.0.0.1:8000/songs \
        -H "Content-Type: application/json" \
        -d '{"title": "순위 오류 테스트", "artist": "리센느", "genre": "팝", "rank": 0}'
"""
# ─────────────────────────────────────────────────────────────────
# 1. import
# ─────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
# BaseModel : pydantic 모든 모델의 부모
# Field : 검증 규칙
from pydantic import BaseModel, Field

app = FastAPI(title = 'POST + Pydantic 예제')

# ─────────────────────────────────────────────────────────────────
# 2. Pydantic 모델 — 요청·응답 분리
# ─────────────────────────────────────────────────────────────────

class SongCreate(BaseModel):
    """POST 요청 본문(Body) 검증용 모델"""
    title: str
    artist: str
    genre: str
    # Field(ge=1) : 1 이상이어야 함.(greater than or equal)
    # 0 이나 음수가 오면 FastAPI가 자동으로 422 응답
    rank: int = Field(ge=1)

# 서버가 클라이언트에게 반환할 데이터 구조
class SongResponse(BaseModel):
    """응답 본문 모델 - id 필가 추가"""
    id: int
    title: str
    artist: str
    genre: str
    rank: int 


# ─────────────────────────────────────────────────────────────────
# 3. 메모리 DB + 다음 id 카운터
# ─────────────────────────────────────────────────────────────────
songs_db: dict[int, dict] = {
    1: {"id": 1, "title": "LOVE ATTACK", "artist": "리센느", "genre": "팝", "rank": 1},
    2: {"id": 2, "title": "갑자기", "artist": "아이오아이", "genre": "팝", "rank": 2},
    3: {"id": 3, "title": "REDRED", "artist": "코르티스", "genre": "팝", "rank": 3},
    4: {"id": 4, "title": "LEMONADE", "artist": "aespa", "genre": "팝", "rank": 4},
    5: {"id": 5, "title": "It's Me", "artist": "아일릿", "genre": "팝", "rank": 5},
    6: {"id": 6, "title": "소문의 낙원", "artist": "악뮤", "genre": "팝", "rank": 6},
}
next_id = 7


# ─────────────────────────────────────────────────────────────────
# 4. GET — 전체 조회
# ─────────────────────────────────────────────────────────────────
# response_model=list[SongResponse]: 응답 형태 자동 검증·문서화

@app.get('/songs', response_model=list[SongResponse])
def list_songs():
    return list(songs_db.values())


# ─────────────────────────────────────────────────────────────────
# 5. GET — 단건 조회
# ─────────────────────────────────────────────────────────────────
@app.get('/songs/{song_id}', response_model=SongResponse)
def get_songs(song_id: int):
    if song_id not in songs_db:
        raise HTTPException(status_code=404, detail='곡을 찾을 수 없습니다.')
    return songs_db[song_id]


# ─────────────────────────────────────────────────────────────────
# 6. POST — 생성
# ─────────────────────────────────────────────────────────────────
# status_code=201: 생성 성공 시 201 Created (POST 의 표준 상태)
@app.post('/songs', response_model=SongResponse, status_code=201)
def create_song(body: SongCreate):
    global next_id

    # rank 중복 체크 - 비즈니스 규칙(한 차트에 같은 순위 두 개 안됨)
    for existing in songs_db.values():
        if existing['rank'] == body.rank:
            # 409 Conflict - 리소스 충돌 시 적절한 상태 코드
            raise HTTPException(
                status_code=409, detail=f'rank {body.rank}은 이미 사용 중입니다.'
            )
    # body.model_dump() : Pydantic 모델 -> dict 변환
    # ** : dict를 키워드 인자로 풀어 결합
    new_song = {'id': next_id, **body.model_dump()}
    songs_db[next_id] = new_song
    next_id += 1
    return new_song


# ─────────────────────────────────────────────────────────────────
# 7. DELETE — 삭제
# ─────────────────────────────────────────────────────────────────
# status_code=204: 삭제 성공 시 204 No Content (응답 본문 없음)

@app.delete("/songs/{song_id}", status_code=204)
def delete_song(song_id:int):
    if song_id not in songs_db:
        raise HTTPException(status_code=404, detail="곡을 찾을 수 없습니다.")
    del songs_db[song_id]
    # return 없음 - 204는 본문 없는 응답이라 자동으로 빈 응답 송신