import streamlit as st

st.set_page_config(page_title="Demo", page_icon="🎈", layout="wide")
st.title("Hello, Streamlit Community Cloud!")
name = st.text_input("Your name?")
st.write(f"Nice to meet you, {name or 'friend'} 👋")