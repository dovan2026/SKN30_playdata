"""간단한 FastAPI 서버"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="docker 이미지 실습용")

class Message(BaseModel):
    text: str

@app.get("/")
def root():
    return {"message":"Hello from FastAPI"}


@app.post("/echo")
def echo(body:Message):
    return {"echo":body.text}