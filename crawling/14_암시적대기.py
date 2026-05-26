from selenium.webdriver import Chrome

driver = Chrome()
driver.get('https://www.weather.go.kr/w/index.do')      # 기상청 사이트를 브라우저에서 연결

# 암시적 대기 설정
# 요소를 찾기 전에 최대 3초까지 기다림
driver.implicitly_wait(3)       # 페이지가 모두 로드될 때까지 최대 3초 대기

# 온도정보 요소 찾음
element = driver.find_element(by='css selector', value='#current-weather span.tmp')

# 요소의 텍스트를 출력
print(element.text)

driver.close()