import requests
from bs4 import BeautifulSoup

url = 'https://finance.naver.com/marketindex/'
market_index = requests.get(url)
print(market_index.status_code)

# soup 객체 만들기
soup = BeautifulSoup(market_index.content, 'html.parser')

# 미션1. 달러 (1488.50) 프린트 해보기

usd = soup.select_one('#exchangeList > li > a.head.usd > div > span.value')
print(f'krw/usd = {usd.text}')

# 미션2. 엔화 (931.98) 프린트 해보기

jpy = soup.select_one('#exchangeList > li > a.head.jpy > div > span.value')
print(f'krw/jpy = {jpy.text}')

# 미션3. 몽골
mnt = soup.select_one('# body > div > table > tbody > tr:nth-child(17) > td.sale')
print(f'krw/mnt = {mnt.text}')