"""03_multi_port — 두 서버를 동시에 띄울 때는 포트를 다르게 지정합니다 (8000 측).

학습 목적:
    같은 머신에서 여러 FastAPI 서버를 동시에 운영하는 방법을 익힙니다.
    핵심은 `--port` 옵션으로 포트를 다르게 주는 것입니다.

main.py 는 포트 8000 (기본값) 으로 실행:
    uvicorn main:app --reload --port 8000

같은 폴더의 chart_server.py 는 별도 터미널에서 8001 로 실행:
    uvicorn chart_server:app --reload --port 8001

확인:
    http://127.0.0.1:8000/      → 멜론 차트 서버 (이 파일)
    http://127.0.0.1:8001/      → 차트 분석 서버 (다른 파일)

`--port` 가 다르므로 두 서버가 충돌하지 않습니다.
"""

from fastapi import FastAPI

# title에 포트 명시
app = FastAPI(title='멜론 차트 서버 - port 8000')

@app.get('/')
def root():
    return {
        'service' : 'melon-chart',
        'port' : 8000,
        'message' : '멜론 차트 서버가 8000번 포트에서 실행 중입니다.'
        }

@app.get('/songs')
def list_songs():
    return [
        {'rank': 1, 'title': "LOVE ATTACK", 'artist': '리센느'},
        {'rank': 2, 'title': "갑자기", 'artist': '아이오아이'},
        {'rank': 3, 'title': "REDRED", 'artist': '코르티스'}
    ]