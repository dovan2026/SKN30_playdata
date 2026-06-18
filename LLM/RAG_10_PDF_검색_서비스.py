from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import streamlit as st
import os
import tempfile

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    except Exception:
        OPENAI_API_KEY = None

if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
else:
    st.error("OPENAI_API_KEY가 없습니다. .env 또는 .streamlit/secrets.toml에 설정해 주세요.")
    st.stop()

st.title("📕📝🔍 PDF 검색 서비스")

# PDF 문서들에서 텍스트 추출
def get_pdf_texts(pdf_docs):
    texts = ""
    for pdf in pdf_docs:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf.getvalue())
            temp_file_path = temp_file.name

        try:
            loader = PyPDFLoader(temp_file_path)
            documents = loader.load()
            texts += "\n".join(doc.page_content for doc in documents)
        finally:
            os.remove(temp_file_path)

    return texts

# 텍스트 청킹
def get_text_chunks(raw_text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=40
    )

    chunks = text_splitter.split_text(raw_text)
    return chunks

# 임베딩 & 벡터DB 생성
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

# 검색된 문서들을 하나의 문자열로 합치는 함수
def format_docs(docs):
    return '\n\n'.join([doc.page_content for doc in docs])

# 체인
def get_conversation_chain(vectorstore):
    llm = ChatOpenAI(
        model='gpt-5.4-mini',
        temperature=0
    )
    promt = PromptTemplate.from_template(
        '''
        다음 검색된 맥락을 사용하여 질문에 답하세요.
        답을 모르면 모른다고 말하세요. 한국어로 답하세요.
        
        # Question : {question}
        # Context : {context}
        # Answer :
        '''
    )
    retriever = vectorstore.as_retriever()
    rag_chain = (
        {'context' : retriever | format_docs,
         'question' : RunnablePassthrough()
         }
         | promt
         | llm
         | StrOutputParser()
    )
    return rag_chain

# PDF 파일 업로드
user_uploads = st.file_uploader('📚PDF 파일 업로드 업로드 해주세요!', accept_multiple_files=True)
if user_uploads:
    if st.button('PDF 업로드 😸'):
        with st.spinner('PDF 처리 중입니다~ 잠시만 기다려주세요! 🫱'):
            # 1. PDF 문서들에서 텍스트 추출
            raw_text = get_pdf_texts(user_uploads) 
            # 2. 텍스트 청크 분할
            text_chunks = get_text_chunks(raw_text)
            # 3. 벡터 저장소 만들기
            vec_1 = get_vectorstore(text_chunks)
            # 4. 대화 체인 만들기
            st.session_state.conversation = get_conversation_chain(vec_1)
        st.success('PDF 업로드 완료!! 대화를 시작해보세요~~🎙️')

# 질문하기
if user_query :=st.chat_input('궁금한 걸 입력해 주세요!! 🎊'):
    if 'conversation' in st.session_state:
        with st.spinner('답변 준비 중입니다~ 잠시만 기다려주세요! 😶‍🌫️'):
            response = st.session_state.conversation.invoke(user_query)
    else:
        response = 'PDF를 먼저 업로드해 주세요!! 🫨'

    with st.chat_message('assistant'):
        st.write(response)
