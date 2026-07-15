# uvicorn server:app --reload
from fastapi import FastAPI

# title에 파일명을 적어둬서 Swagger에서 어느 파일이 떴는지 즉시 확인
app = FastAPI(title='멜론 API - server.py')

@app.get('/')
def root():
    # response에 파일명을 함께 담아 클라이언트가 어느 서버인지 알 수 있게
    return {'file':'server.py', 'message':'server 파일에서 실행되었습니다.'}
