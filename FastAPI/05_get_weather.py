from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title = '날씨 조회 API 만들기 실습')

weather_db = {
    1: {'city': '서울', 'temperature': '27도'},
    2: {'city': '부산', 'temperature': '33도'}
}

@app.get('/weather')
def root(city: str):
    for weather in weather_db.values():
        if weather['city'] == city:
            temperature = weather['temperature']
    return {'message': f'안녕하세요, {city}의 온도는 {temperature}입니다.'}