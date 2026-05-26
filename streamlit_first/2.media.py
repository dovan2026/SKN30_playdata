import streamlit as st
import time

st.title('Media elements')
st.caption('text 참고사이트: https://docs.streamlit.io/library=api-reference/media')

st.header("Media elements")
# 버튼을 누를 때마다 랜덤 이미지
if st.button('랜덤 이미지'):
    random_url = f'https://picsum.photos/200/300?random={time.time()}'
    st.image(random_url)
# 로컬 mp3 파일을 재생
st.header('2.Audio')
st.audio('./data/MusicSample.mp3')

# 로컬 mp4 파일을 재생
st.header('3.Video')
st.video('./data/VideoSample.mp4')
