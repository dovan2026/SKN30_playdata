# 1. 라이브러리 불러오기
import requests
import pandas as pd
from bs4 import BeautifulSoup

# 2. html 요소 얻기
# 봇 차단 방지 헤더 추가 (https://www.whatismybrowser.com/detect/what-is-my-user-agent/)
header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
url = "https://www.melon.com/chart/index.htm" # 멜론 top100주소
page = requests.get(url, headers=header)

# 3. BeatifulSoup 으로 파싱
bs_result = BeautifulSoup(page.text, "html.parser")
bs_result

# 결과물을 저장할 리스트 생성
result_list = [] 

copy_selector = "#frm > div > table > tbody"
data = bs_result.select(copy_selector+ "> tr")
print(len(data))

# 리스트로 저장
result_list = [] 

for item in data:
    tmp_list = item.find_all('td')
    text = tmp_list[5].get_text(separator='_', strip=True)
    text_list = text.split('_')

    tmp_dict = {}
    tmp_dict['title'] = text_list[0]
    tmp_dict['artist'] = text_list[1]
    result_list.append(tmp_dict)

# 리스트 -> 데이터프레임 변환
df = pd.DataFrame(result_list)

# CSV 파일 저장
df.to_csv("melon_hot100.csv", index=False, encoding="utf-8-sig")
