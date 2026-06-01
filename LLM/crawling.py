import time
import csv
import re
import os
from datetime import datetime, date, timedelta
import pandas as pd

# selenium 관련 라이브러리 (방법 B용)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# google-play-scraper 라이브러리 (방법 A용)
try:
    from google_play_scraper import reviews, Sort
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False

TARGET_DATE = date(2026, 5, 30)
TARGET_DATE_STR = "2026년 5월 30일"

def is_target_date(date_text):
    """
    날짜 텍스트가 정확히 '2026년 5월 30일'에 해당하는지 정밀 검증합니다.
    (현재 로컬 시각 2026년 6월 1일 기준, 상대적 날짜인 '2일 전' 도 동일한 날짜로 간주합니다.)
    """
    clean_date = date_text.strip()
    
    # 1. 절대적인 날짜 표현 매칭 ("2026년 5월 30일", "2026. 5. 30")
    if "2026년 5월 30일" in clean_date:
        return True
        
    normalized = clean_date.replace(" ", "")
    if "2026.5.30" in normalized or "26.5.30" in normalized:
        return True
        
    # 2. 정규식 활용 년/월/일 파싱 매칭
    if re.search(r'(20)?26[\s\.\-년]+0?5[\s\.\-월]+30', clean_date):
        return True
        
    # 3. 상대적인 날짜 표현 매칭 (현재 2026년 6월 1일 기준 이틀 전 = 5월 30일)
    if "2일 전" in clean_date or "2일전" in clean_date or "2 days ago" in clean_date:
        return True
        
    return False

def is_past_date(date_text):
    """
    날짜 텍스트가 타겟 날짜(2026년 5월 30일)보다 확실한 과거인지 판별하여 스크롤을 조기 종료할 때 사용합니다.
    (현재 2026년 6월 1일 기준, 3일 전 이상의 상대 날짜 혹은 5월 29일 이하의 날짜)
    """
    clean_date = date_text.replace(" ", "")
    
    # 1. 상대적인 날짜 형식의 과거 판정 (3일 전, 4일 전, 1주일 전, 1달 전 등)
    past_relative_patterns = [
        "3일전", "4일전", "5일전", "6일전", "7일전", "8일전", "9일전", "10일전", "일주일전", "주전", "달전", "개월전", "년전",
        "3daysago", "4daysago", "5daysago", "6daysago", "7daysago", "weekago", "monthago", "yearago"
    ]
    for pattern in past_relative_patterns:
        if pattern in clean_date:
            return True
            
    # 2. 절대적인 날짜 형식의 과거 판정 (정규식 년, 월, 일 분석)
    match = re.search(r'(20)?(26|25|24)[\s\.\-년]+(0?[1-9]|1[0-2])[\s\.\-월]+(0?[1-9]|[12][0-9]|3[01])', clean_date)
    if match:
        year = int(match.group(2))
        month = int(match.group(3))
        day = int(match.group(4))
        
        # 2026년 5월 30일보다 확실한 과거 조건
        if year < 26:
            return True
        if year == 26 and month < 5:
            return True
        if year == 26 and month == 5 and day < 30:
            return True
            
    # 3. 특정 한글 날짜 텍스트 패턴 과거 판정
    past_absolute_patterns = ["5월29일", "5월28일", "5월27일", "5월26일", "4월", "3월", "2월", "1월", "2025년", "2024년"]
    for pattern in past_absolute_patterns:
        if pattern in clean_date:
            return True
            
    return False

def crawl_via_scraper():
    """
    방법 A: google-play-scraper 라이브러리를 사용한 초고속/안정적 크롤링
    """
    if not SCRAPER_AVAILABLE:
        print("google-play-scraper 라이브러리가 설치되어 있지 않습니다.")
        return None
        
    print("\n[방법 A] google-play-scraper를 사용하여 크롤링을 시작합니다...")
    
    # 토스 앱의 Google Play 패키지 ID: viva.republica.toss
    app_id = 'viva.republica.toss'
    
    all_reviews = []
    continuation_token = None
    target_count = 1000 # 넉넉하게 최근 1000개 수집
    
    print(f"최근 리뷰 {target_count}개를 API로 직접 가져옵니다. (매우 빠름)...")
    
    result, continuation_token = reviews(
        app_id,
        lang='ko',     # 한국어 리뷰
        country='kr',   # 한국 플레이스토어
        sort=Sort.NEWEST, # 최신순 정렬
        count=target_count
    )
    
    filtered_reviews = []
    seen_keys = set()
    
    for r in result:
        # r['at']는 datetime 객체입니다. (UTC 또는 로컬 타임)
        # 로컬 시간 기준 날짜로 변환하여 2026-05-30에 해당하는지 필터링합니다.
        review_date = r['at'].date()
        
        if review_date == TARGET_DATE:
            author = r['userName']
            rating = r['score']
            content = r['content']
            date_text = r['at'].strftime("%Y-%m-%d %H:%M:%S")
            
            review_key = (author, content)
            if review_key not in seen_keys:
                seen_keys.add(review_key)
                filtered_reviews.append({
                    "작성자": author,
                    "평점": rating,
                    "날짜": date_text,
                    "리뷰내용": content
                })
                
    print(f"API 수집 완료! 2026년 5월 30일 리뷰 총 {len(filtered_reviews)}개 필터링됨.")
    return pd.DataFrame(filtered_reviews)

def crawl_via_selenium():
    """
    방법 B: Selenium 웹 드라이버를 사용하여 브라우저 제어 및 모달 스크롤 크롤링
    """
    print("\n[방법 B] Selenium 브라우저 자동화를 사용하여 크롤링을 시작합니다...")
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')  # 백그라운드 실행
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('lang=ko_KR')  # 한국어 페이지 강제
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        url = "https://play.google.com/store/apps/details?id=viva.republica.toss"
        driver.get(url)
        print("토스 플레이스토어 페이지 로딩 중...")
        time.sleep(3.5)
        
        # 1. 리뷰 섹션으로 스크롤 다운
        print("리뷰 버튼 활성화를 위해 스크롤 다운 중...")
        for i in range(4):
            driver.execute_script("window.scrollTo(0, 1000 + arguments[0] * 500);", i)
            time.sleep(1.0)
            
        # 2. '리뷰 모두 보기' 버튼 찾기 및 클릭
        print("리뷰 모달창 여는 중...")
        show_all_reviews_btn = None
        try:
            show_all_reviews_btn = driver.find_element(
                By.XPATH, "//button[contains(., '리뷰 모두 보기') or contains(., '리뷰 전체 보기') or contains(., 'See all reviews')]"
            )
        except Exception:
            raise Exception("리뷰 전체 보기 버튼을 찾을 수 없습니다. (웹페이지 레이아웃 변경 가능성)")
            
        driver.execute_script("arguments[0].click();", show_all_reviews_btn)
        time.sleep(4.0)
        
        # 3. 스크롤 container와 정렬 dropdown 찾기
        dialog = driver.find_element(By.CSS_SELECTOR, "div.VfPpkd-Sx9Kwc")
        scroll_container = dialog.find_element(By.CSS_SELECTOR, "div.fysCi")
        
        # 4. 정렬 필터를 '최신순'으로 변경
        print("정렬 필터를 '최신순'으로 변경합니다...")
        sort_div = None
        role_buttons = dialog.find_elements(By.XPATH, ".//div[@role='button']")
        for d in role_buttons:
            text = d.text.strip()
            if "관련성" in text or "Most relevant" in text or "정렬" in text or "Sort" in text:
                sort_div = d
                break
                
        if sort_div:
            driver.execute_script("arguments[0].click();", sort_div)
            time.sleep(2.0)
            
            # '최신순' 메뉴 아이템 클릭
            menu_items = driver.find_elements(
                By.XPATH, "//div[@role='menuitem'] | //span[@role='menuitem'] | //div[contains(@class, 'ypTNYd')] | //span[contains(text(), '최신')] | //div[contains(text(), '최신')]"
            )
            clicked_newest = False
            for item in menu_items:
                text = item.text.strip()
                if "최신" in text or "Newest" in text or "Most recent" in text:
                    driver.execute_script("arguments[0].click();", item)
                    print("정렬 필터를 '최신순'으로 변경 완료!")
                    clicked_newest = True
                    time.sleep(3.5)
                    break
            if not clicked_newest:
                print("최신순 옵션을 찾지 못해 기본 정렬 상태로 진행합니다.")
        else:
            print("정렬 버튼을 찾지 못해 기본 정렬 상태로 진행합니다.")
            
        # 5. 모달 내부 동적 스크롤 (조기 종료 기능 포함)
        print("2026년 5월 30일 리뷰 탐색을 위해 스크롤을 시작합니다...")
        
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
        
        while True:
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
            time.sleep(2.0)
            
            # 스크롤 최적화: 현재 로드된 리뷰들의 날짜를 확인하고, 
            # 2026년 5월 30일 이전의 과거 데이터가 다수 보이면 스크롤을 조기 종료합니다.
            date_elements = scroll_container.find_elements(By.CSS_SELECTOR, "span.bp9Aid")
            if date_elements:
                recent_dates = [el.text for el in date_elements[-15:] if el.text]
                past_in_recent = [date for date in recent_dates if is_past_date(date)]
                
                if len(past_in_recent) >= 12:
                    print("2026년 5월 30일 이전의 과거 리뷰 영역에 도달했습니다. 스크롤을 중지합니다.")
                    break
                    
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            if new_height == last_height:
                time.sleep(2.0)
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
                new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
                if new_height == last_height:
                    print("더 이상 추가 리뷰가 로드되지 않습니다.")
                    break
            last_height = new_height
            
        # 6. 로드된 데이터에서 '2026년 5월 30일'에 작성된 리뷰 정밀 추출
        print("\n데이터 정밀 필터링 및 수집 시작...")
        
        reviews_data = []
        seen_reviews = set()
        
        # 리뷰 카드 엘리먼트들 (RHo1pe 클래스)
        review_cards = scroll_container.find_elements(By.CSS_SELECTOR, "div.RHo1pe")
        
        for card in review_cards:
            try:
                date_element = card.find_element(By.CSS_SELECTOR, "span.bp9Aid")
                date_text = date_element.text
            except Exception:
                continue
                
            # 타겟 날짜 '2026년 5월 30일' (혹은 '2일 전')이 맞는지 필터링
            if not is_target_date(date_text):
                continue
                
            try:
                author = card.find_element(By.CSS_SELECTOR, "div.X5PpDu").text
            except Exception:
                author = "알 수 없음"
                
            try:
                star_element = card.find_element(By.CSS_SELECTOR, "div.i1P3Qe")
                star_text = star_element.get_attribute("aria-label")
                rating = star_text.split("만점에 ")[1].replace("개", "").strip() if "만점에" in star_text else star_text
            except Exception:
                rating = "N/A"
                
            try:
                content = card.find_element(By.CSS_SELECTOR, "div.h3YV2d").text
            except Exception:
                content = ""
                
            if content:
                review_key = (author, content)
                if review_key not in seen_reviews:
                    seen_reviews.add(review_key)
                    reviews_data.append({
                        "작성자": author,
                        "평점": rating,
                        "날짜": f"{TARGET_DATE_STR} ({date_text})",
                        "리뷰내용": content
                    })
                    
        print(f"Selenium 수집 완료! 2026년 5월 30일 리뷰 총 {len(reviews_data)}개 수집됨.")
        return pd.DataFrame(reviews_data)
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    print("="*60)
    print("      Toss App Store Review Crawler (Date: 2026-05-30)      ")
    print("="*60)
    
    df_reviews = None
    
    # 1. google-play-scraper 라이브러리가 있을 경우 방법 A 우선 시도 (극히 권장)
    if SCRAPER_AVAILABLE:
        try:
            df_reviews = crawl_via_scraper()
        except Exception as err:
            print(f"API 크롤러 실행 오류로 인해 Selenium 방법으로 대체합니다: {err}")
            
    # 2. 방법 A가 실패했거나 라이브러리가 없는 경우 Selenium 방법 B 실행
    if df_reviews is None or df_reviews.empty:
        df_reviews = crawl_via_selenium()
        
    # 3. CSV 파일로 최종 저장
    if df_reviews is not None and not df_reviews.empty:
        filename = "toss_reviews_20260530.csv"
        # 한글 깨짐 방지를 위해 utf-8-sig로 저장합니다.
        df_reviews.to_csv(filename, index=False, encoding="utf-8-sig")
        print("="*60)
        print(f"축하합니다! 크롤링 데이터가 '{filename}' 파일로 저장되었습니다.")
        print(f"수집된 고유 리뷰 수: {len(df_reviews)}개")
        print("="*60)
        
        # 미리보기 출력
        print("\n=== 수집된 리뷰 미리보기 (상위 5개) ===")
        print(df_reviews.head())
    else:
        print("="*60)
        print("데이터를 성공적으로 수집 및 필터링하지 못했습니다.")
        print("="*60)
