"""04_get_params — 음악 차트 데이터로 배우는 GET 요청 파라미터 9가지 패턴.

이 파일은 음악 차트 데이터로 GET 파라미터 패턴 9가지를 연습하도록 구성했습니다.

실행:
    uvicorn main:app --reload

브라우저로 직접 확인:
    /                                       → 사용 가능한 엔드포인트 목록
    /hello?name=민수                         → 인사 (Query 가장 단순)
    /songs/1                                → Path 단건 조회
    /songs                                  → Query 기본값 사용 (limit=10)
    /songs?limit=3                          → Query 1개
    /songs?limit=2&genre=팝                  → Query 여러 개
    /songs?artist=aespa                     → Optional Query
    /calc?a=10&b=20                         → 자동 타입 변환 (str → int)
    /search?keyword=악뮤                     → 필수 Query (없으면 422)
    /songs/sorted?sort=rank&page=1&size=3   → 페이징 + 정렬
    /artists/aespa/songs?limit=1            → Path + Query 조합

Swagger UI 에서 한 번에 테스트:
    http://127.0.0.1:8000/docs
"""
# ─────────────────────────────────────────────────────────────────
# 1. import + 앱 인스턴스
# ─────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException

app = FastAPI(title = "음악 차트 GET 파라미터 예제")


# ─────────────────────────────────────────────────────────────────
# 2. 메모리 데이터 — 모든 엔드포인트가 이 데이터를 사용합니다
# ─────────────────────────────────────────────────────────────────
# 실제 서비스에서는 DB 에서 조회하지만 학습용으로는 메모리 dict 가 충분합니다
songs_db = {
    1: {"id": 1, "title": "LOVE ATTACK", "artist": "리센느", "genre": "팝", "rank": 1},
    2: {"id": 2, "title": "갑자기", "artist": "아이오아이", "genre": "팝", "rank": 2},
    3: {"id": 3, "title": "REDRED", "artist": "코르티스", "genre": "팝", "rank": 3},
    4: {"id": 4, "title": "LEMONADE", "artist": "aespa", "genre": "팝", "rank": 4},
    5: {"id": 5, "title": "It's Me", "artist": "아일릿", "genre": "팝", "rank": 5},
    6: {"id": 6, "title": "소문의 낙원", "artist": "악뮤", "genre": "팝", "rank": 6},
}


# ─────────────────────────────────────────────────────────────────
# 3. 루트 — 사용 가능한 엔드포인트 안내
# ─────────────────────────────────────────────────────────────────
@app.get('/')
def root():
    return {
        "message": '음악 차트로 배우는 GET 파라미터 예제 서버',
        "try": [
            "/hello?name=민수",
            "/songs/1",
            "/songs?limit=3&genre=팝",
            "/calc?a=10&b=20",
            "/search?keyword=악뮤",
            "/songs/sorted?sort=rank&page=1&size=3",
            "/artists/aespa/songs?limit=1",
        ],
    }


# ─────────────────────────────────────────────────────────────────
# 4. 가장 단순한 Query — 인사말
# ─────────────────────────────────────────────────────────────────
# URL 형식: GET /hello?name=민수
# 안녕하세요, 민수님!!

# name:str는 함수 인자에 타입 힌트만 적은 것
# 경로(/hello) 안에 {name}이 없으므로 FastAPI가 자동으로 Query 파라미터로 인식함.
@app.get('/hello')
def say_hello(name:str):
    return {'message': f'안녕하세요, {name}님!!'}





# ─────────────────────────────────────────────────────────────────
# 5. Query 기본값 + 여러 개 + Optional
# ─────────────────────────────────────────────────────────────────
# 한 함수에서 3가지 패턴을 모두 보여줍니다.
# URL 시나리오: 
#   GET /songs
#   GET /songs?limit=3
#   GET /songs?limit=2&genre=팝
#   GET /songs?artist=aespa

@app.get('/songs')
def list_songs(
    limit: int = 10,                # 반환할 최대 곡 개수, 생략하면 기본값 10
    genre: str | None = None,       # 장르 검색 조건, 생략하면 장르 필터링 안함
    artist: str | None = None
):
    # songs_db의 모든 value를 가져와 새로운 리스트로
    result = list(songs_db.values())

    # genre가 URL에 전달된 경우에만 해당 장르의 곡을 남김
    if genre is not None:
        result = [s for s in result if s['genre'] == genre]

    # artist가 URL에 전달된 경우에만 해당 가수의 곡을 남김
    if artist is not None:
        result = [s for s in result if s['artist'] == artist]

    # 필터링이 끝난 결과에서 앞쪽 limit개만 반환
    return result[:limit]



# ─────────────────────────────────────────────────────────────────
# 6. 자동 타입 변환
# ─────────────────────────────────────────────────────────────────
# URL: GET /calc?a=10&b=20
#
# 핵심 포인트: URL 쿼리 문자열은 항상 문자열입니다 ("10", "20").
# 그런데 함수에서 a: int, b: int 라고 선언하면 FastAPI 가 자동으로 int 로 변환해줍니다.
# 변환 못 하는 값(/calc?a=abc) 이 오면 422 자동 응답.

@app.get('/calc')
def calculate(a: int, b: int):
    return {
        'a':a,
        'b':b,
        'sum':a+b,
        'product':a*b
    }



# ─────────────────────────────────────────────────────────────────
# 7. 필수 Query (기본값 없음)
# ─────────────────────────────────────────────────────────────────
# URL 시나리오:
#   GET /search?keyword=악뮤          → 악뮤의 곡 검색
#   GET /search?keyword=LOVE          → 제목이 LOVE ATTACK인 곡 검색
#   GET /search                      → 422 (keyword 가 필수인데 없음)

# 1. 검색 결과 없는 경우 확인
# 2. 제목 전용 검색, 가수 전용 검색
# 3. 검색 결과 개수 제한 -> 장르 : 팝 -> 2개만 반환

@app.get('/search')
def search_song(keyword: str):
    # 단순 검색 : 제목 또는 가수에 keyword가 포함되면 매칭
    keyword_lower = keyword.lower()
    result = [
        s
        for s in songs_db.values()
        if keyword_lower is s['title'].lower() or keyword_lower in s['artist'].lower()
    ]
    return {'keyword': keyword, 'count': len(result), 'result': result}


# ─────────────────────────────────────────────────────────────────
# 8. 페이징 + 정렬 (현실적인 패턴)
# ─────────────────────────────────────────────────────────────────
# URL: GET /songs/sorted?sort=rank&page=1&size=3

# 큰 데이터를 페이지 단위로 나눠 보내는 가장 일반적인 패턴.
@app.get('/songs/sorted')
def list_songs_sorted(sort: str = 'rank', page: int = 1, size: int = 5):
    # 정렬
    sorted_songs = sorted(songs_db.values(), key = lambda s: s.get(sort, 0))

    # 페이징 : offset 계산(1 페이지면 0, 2 페이지면 size, ...)
    offset = (page - 1) * size

    return {
        'page' : page,
        'size' : size,
        'sort' : sort,
        'result' : sorted_songs[offset : offset + size]
    }



# ─────────────────────────────────────────────────────────────────
# 9. Path 파라미터 — 단건 조회
# ─────────────────────────────────────────────────────────────────
# URL 형식: GET /songs/1 → 차트 1위 LOVE ATTACK 반환
#
# 경로 안 {song_id} 와 함수 인자 song_id 가 같은 이름이면 Path 파라미터입니다.
# `song_id: int` 라고 쓰면 FastAPI 가 자동으로 int 변환 + 검증을 해줍니다.
# (예: /songs/abc 처럼 오면 422 자동 응답)

@app.get('/songs/{song_id}')
def get_song(song_id: int):
    if song_id not in songs_db:
        # HTTPException - 의도적으로 404 응답을 만듭니다.
        raise HTTPException(status_code=404, detail='곡을 찾을 수 없습니다.')
    return songs_db[song_id]



# ─────────────────────────────────────────────────────────────────
# 10. Path + Query 조합
# ─────────────────────────────────────────────────────────────────
# URL: GET /artists/aespa/songs?limit=1
#
# 경로의 {artist_name}에는 "aespa", Query의 limit에는 1이 전달됩니다.
# {artist_name} 은 Path, 함수의 다른 인자 limit 은 Query 입니다.
# 두 가지가 함께 쓰이는 가장 흔한 형태입니다.

@app.get('/artists/{artist_name}/songs')
def list_artist_songs(artist_name: str, limit: int = 5):
    result = [s for s in songs_db.values() if s['artist'] == artist_name]
    return {
        'artist': artist_name,
        'count': len(result),
        'result': result[:limit]
    }
