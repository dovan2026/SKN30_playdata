from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions as EC        # 기다릴 조건들
from selenium.webdriver.support.ui import WebDriverWait                 # 기다리는 도구

driver = Chrome()
driver.get('https://www.weather.go.kr/w/index.do')      # 기상청 사이트를 브라우저에서 연결

# 명시적 대기 설정
# 최대 5초 동안 특정 요소가 나타날 때까지 기다림
wait = WebDriverWait(driver, 5)

# 조건
element = wait.until(
    EC.presence_of_element_located(('css selector', '#current-weather span.tmp'))
)

print(element.text)     # 요소의 텍스트를 출력

driver.close()