"""01_hello - 가장 단순한 FastAPI 서버

학습 목적:
    FastAPI 의 가장 작은 구조를 확인합니다.
    1) FastAPI 인스턴스 생성
    2) @app.get 데코레이터로 엔드포인트 정의
    3) 함수가 반환한 dict 가 자동으로 JSON 응답이 됨

설치:
    uv add fastapi uvicorn[standard]

실행:
    cd 01_hello
    uvicorn main:app --reload

`uvicorn main:app` 의 의미:
    main = 파일명 (main.py 의 .py 빼고)
    app  = FastAPI 인스턴스 변수명 (아래 `app = FastAPI(...)` 의 변수)

확인:
    http://127.0.0.1:8000/         → {"message": "Hello MTVS"}
    http://127.0.0.1:8000/health   → {"status": "ok"}
    http://127.0.0.1:8000/docs     → Swagger UI (브라우저에서 직접 테스트)
"""

from fastapi import FastAPI

# FastAPI 인스턴스 생성
app = FastAPI()

# @app.get('/') : GET 메서드로 '/' 경로 요청을 이 함수가 처리하라는 데코레이터
@app.get("/")
def root():
    return {"message": "Hello SKN30"}

# 헬스 체크 엔드 포인트 - 서버 살아있는지 확인용
@app.get('/health')
def health():
    return {"status": "ok"}

# 날씨 엔드 포인트
# weather. return '여름입니다.'
@app.get('/weather')
def weather():
    return '여름입니다. 너무 더워요.'

# city 날씨
@app.get('/weather/city')
def city(city:str):
    return f'{city}는 이제 많이 더워요'

items = {
    0: {'name': 'bread',
        'price': 2000},
    1: {'name': 'water',
        'price': 1000},
    2: {'name': '라면',
        'price': 3500}
}

# 전체 아이템을 가져오고 싶을 때
@app.get('/items')
def read_all_item():
    return
# http://127.0.0.1:8000/items -> 전체 item 조회

# item_id로 라면을 조회
@app.get('items/{item_id}')
def read_item(item_id: int):
    item = items[item_id]
    return item
# http://127.0.0.1:8000/items/2 -> items 라면 조회

# /items/10 -> 경로 매개변수 : 특정 상품 조회
# /items?category=book -> 쿼리 매개변수 : 조건으로 상품 검색