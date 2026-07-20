from langchain_openai import ChatOpenAI
from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv(override=True)
openai_api_key= os.getenv("OPENAI_API_KEY")

app = FastAPI()

# openai_api를 이용해서 모델 정의
model = ChatOpenAI(
    api_key=openai_api_key,
    model = "gpt-4.1-mini",
    temperature=0.4
)

@app.post("/chatbot/{character}")
def chatbot(text:str, character:str):
    answer = model.invoke(f"{character}에 대해서 {text}")
    return {'question': f"{character}에 대해서 {text}", "ai_message":answer.content}