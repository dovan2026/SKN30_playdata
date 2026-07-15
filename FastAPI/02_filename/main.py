"""02_filename — 파일명을 바꿔도 똑같이 동작합니다.

이 폴더에 같은 코드를 main.py / server.py / api.py 세 가지 이름으로 생성합니다.
파일명만 다를 뿐 코드 내용은 동일합니다.

핵심 학습:
    `uvicorn 파일명:앱변수명` — 콜론 앞이 파일명, 뒤가 FastAPI() 인스턴스 변수명입니다.
    main.py 가 아니어도 됩니다. server.py, api.py, melon.py 모두 가능.

실행 (각각 다른 터미널에서 또는 차례로):
    uvicorn main:app --reload      ← 이 파일
    uvicorn server:app --reload    ← 같은 폴더의 server.py
    uvicorn api:app --reload       ← 같은 폴더의 api.py

응답 본문에 어느 파일에서 실행됐는지 표시되어 있어 한눈에 구분됩니다.
"""

from fastapi import FastAPI

# title에 파일명을 적어둬서 Swagger에서 어느 파일이 떴는지 즉시 확인
app = FastAPI(title='멜론 API - main.py')

@app.get('/')
def root():
    # response에 파일명을 함께 담아 클라이언트가 어느 서버인지 알 수 있게
    return {'file':'main.py', 'message':'main 파일에서 실행되었습니다.'}
