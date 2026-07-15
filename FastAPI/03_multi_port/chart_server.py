"""03_multi_port — 두 번째 서버는 포트 8001 로 띄웁니다.

별도 터미널 (main.py 가 8000 으로 떠 있는 상태) 에서:
    uvicorn chart_server:app --reload --port 8001

같은 머신에서 두 FastAPI 서버가 충돌 없이 동시에 실행됩니다.

만약 둘 다 같은 포트로 띄우려고 하면 둘째 서버는
    OSError: [Errno 48] Address already in use
같은 에러가 납니다 — 이게 "포트 충돌" 입니다.
"""

from fastapi import FastAPI

app = FastAPI(title='차트 분석 서버 - port 8001')

@app.get('/')
def root():
    return {
        'service' : 'chart-analytics',
        'port' : 8001,
        'message' : '차트 분석 서버가 8001번 포트에서 실행 중입니다.'
        }

@app.get('/stats')
def chart_stats():
    return {
        'total_songs' : 100,
        'top_artist' : '악뮤',
        'top_genre' : '팝'
    }