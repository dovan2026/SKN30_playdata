import base64
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_openai_api_key():
    try:
        return st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


st.title("제품 홍보 포스터 생성기")

keyword = st.text_input("키워드를 입력하세요")

if st.button("생성하기"):
    if not keyword.strip():
        st.warning("키워드를 입력하세요.")
    else:
        api_key = get_openai_api_key()
        if not api_key:
            st.error("OPENAI_API_KEY를 .streamlit/secrets.toml 또는 .env에 설정하세요.")
            st.stop()

        client = OpenAI(api_key=api_key)

        with st.spinner("생성 중입니다..."):
            response = client.responses.create(
                model="gpt-4.1-mini",
                instructions=(
                    "입력받은 키워드에 대해 150자 이내의 제품 홍보 문구를 작성하세요."
                ),
                input=keyword,
            )

            result = response.output_text

            img = client.images.generate(
                model="gpt-image-2",
                prompt=f"제품 홍보 포스터 이미지. 키워드: {keyword}. 홍보 문구: {result}",
                size="1024x1024",
            )

        st.write(result)

        image_bytes = base64.b64decode(img.data[0].b64_json)
        st.image(image_bytes, width=500)

        with open("output.png", "wb") as f:
            f.write(image_bytes)
