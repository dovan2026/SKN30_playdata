from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title = '날씨 조회 API 만들기 실습')

weather_db = {
    1: {'city': '서울', 'temperature': '27도'},
    2: {'city': '부산', 'temperature': '33도'}
}

@app.get('/weather')
def root(city: str):
    return 