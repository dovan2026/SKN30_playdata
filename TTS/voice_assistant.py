import speech_recognition as sr
from openai import OpenAI
import os

client = OpenAI()

SYSTEM_PROMPT = """너는 이런 성격의 캐릭터야.

영화 인사이드 아웃에 나오는 기쁨이 캐릭터
작고 귀여운 외모: 귀여운 얼굴과 작은 체구가 특징이에요.
활발한 성격: 언제나 에너지가 넘치고 활발하게 움직여요.
호기심이 많음: 새로운 물건이나 사람에게 호기심이 많아 관심을 보이며 탐색해요.
사람을 좋아함: 사람들과의 교류를 좋아하고 관심을 받는 것을 즐겨요.
훈련을 잘 따름: 간식이나 칭찬에 민감해 훈련을 잘 따르고 순종적이에요.
잘 먹음: 음식을 좋아하고 식욕이 왕성해요.
놀기 좋아함: 공이나 장난감을 가지고 노는 것을 즐기며 활발하게 뛰어다녀요.
온화한 성격: 화를 잘 내지 않고 온화한 성격이에요."""

recognizer = sr.Recognizer()

def transcribe_audio(recognizer, phrase_time_limit=5, timeout=10):
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("말씀해주세요...")
        try:
            audio = recognizer.listen(source, phrase_time_limit=phrase_time_limit, timeout=timeout)
            return recognizer.recognize_google(audio, language="ko-KR")
        except sr.UnknownValueError:
            print("음성을 이해하지 못했습니다.")
            return None
        except sr.RequestError as e:
            print(f"음성 인식 요청 실패: {e}")
            return None

def ask_openai(user_text):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()

print("음성 에이전트가 시작되었습니다. 종료하려면 '종료'라고 말하세요.")

while True:
    user_text = transcribe_audio(recognizer)
    if user_text is None:
        print("음성을 인식하지 못했습니다. 다시 시도해주세요.")
        continue

    print("사용자:", user_text)
    if "종료" in user_text or "그만" in user_text:
        print("에이전트를 종료합니다.")
        break

    answer_text = ask_openai(user_text)
    print("[AI 답변]:", answer_text)
