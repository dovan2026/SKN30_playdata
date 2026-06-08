import os
import pandas as pd
import ast
from dotenv import load_dotenv
import streamlit as st
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.tools import BaseTool, Tool, tool
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import ChatMessage
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.vectorstores import LanceDB
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import lancedb
from langchain.chains import RetrievalQA


st.set_page_config(page_title="MovieMate", page_icon="🎬")
st.header('🎬 MovieMate에 오신 것을 환영합니다. 딱 맞는 영화를 추천해 드리겠습니다.')

# load_dotenv()

# openai_api_key = os.environ['OPENAI_API_KEY']

# embeddings = 
# uri = 
# db = 

# table = 
# docsearch = 

# # 영화 데이터셋 불러오기
# md = pd.read_pickle('movies.pkl')

# # 사용자 입력을 위한 사이드바 생성
# st.sidebar.title("영화 추천 시스템")
# st.sidebar.markdown("아래에 정보를 입력해주세요:")

# # 사용자에게 나이, 성별 및 선호 영화 장르를 묻기
# age = st.sidebar.slider("나이를 선택하세요", 1, 100, 25)
# gender = st.sidebar.radio("성별을 선택하세요", ("Male", "Female", "Other"))
# genre = st.sidebar.selectbox("선호하는 영화 장르를 선택하세요", md.explode('genres')["genres"].unique())


# # 사용자 입력을 기반으로 영화를 필터링
# df_filtered = md[md['genres'].apply(lambda x: genre in x)]


# template_prefix = """


# """

# user_info = """


# """

# template_suffix= """


# """

# user_info = user_info.format(age = age, gender = gender)

# COMBINED_PROMPT = template_prefix +'\n'+ user_info +'\n'+ template_suffix
# print(COMBINED_PROMPT)

# # 체인 설정
# qa = 

# query = st.text_input('질문을 입력하세요:', placeholder = '어떤 액션 영화를 추천해 주시겠어요?')
# if query:
#     result = qa.invoke({"query": query})
#     st.write(result['result'])
