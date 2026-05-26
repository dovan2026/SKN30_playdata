import streamlit as st
import random

st.title('오늘의 운세를 알아보아요~')
error_msg = '"김OO"처럼 성함을 정확히 적어주세요.'

name = st.text_input('당신의 이름은?', value = '김OO')  

list_fortune = ['오늘은 새로운 도전을 해보기에 좋은 날입니다.',
'작은 실수가 있어도 너무 걱정하지 마세요.',
'좋은 아이디어가 떠오를 수 있습니다.',
'오늘은 휴식이 필요한 날입니다.',
'주변 사람과의 대화에서 좋은 기회를 얻을 수 있습니다.']

if st.button('운세 보기') == False:
    pass
     
elif name == '' or name == '김OO':
    st.warning(error_msg)
    
else:
    fortune = random.choice(list_fortune)

    # [수정] f-string
    st.write(f'### ✨ {name}님, 오늘의 운세는')
    st.success(fortune)
    st.balloons()