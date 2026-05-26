import requests
from bs4 import BeautifulSoup

# 처음 서버가 보내준 HTML만 가져옴
# <흐름>
# 1. 브라우저가 기본 HTML을 먼저 받고
# 2. 화면 틀만 먼저 보입니다.
# 3. 자바스크립트가 백그라운드에서 날씨 데이터 등을 다시 요청합니다.
# 4. 받은 데이터를 페이지에 끼워 넣습니다.

response = requests.get('https://www.weather.go.kr/w/index.do')
print(response.status_code)

soup = BeautifulSoup(response.content, 'html.parser')
print(soup.select('.tmp')) # Selenium으로 해야함

      