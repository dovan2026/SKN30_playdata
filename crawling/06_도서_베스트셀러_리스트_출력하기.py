import requests
from bs4 import BeautifulSoup

# 도서 정보를 저장할 클래스 선언
class Book:
    def __init__(self, rank, title, author, price):
        self.rank = rank
        self.title = title
        self.author = author
        self.price = price

    def __str__(self):
        return f'{self.rank}, {self.title}, {self.author}, {self.price}'
    
    def to_dict(self):
        return {'rank':self.rank, 'title':self.title, 'author':self.author, 'price':self.price}
    
    def to_list(self):
        return [self.rank, self.title, self.author, self.price]


url = 'https://www.yes24.com/Product/Category/BestSeller?categoryNumber=001'
bestseller = requests.get(url)
soup = BeautifulSoup(bestseller.content, 'html.parser')

best_list = soup.select('#yesBestList div.item_info')
print(len(best_list))

#yesBestList > li:nth-child(1) > div > div.item_info

book_list = []

for i, item in enumerate(best_list):
    title = item.select_one('div.info_name > a').text
    author = item.select_one('.info_auth > a').text
    price = item.select_one('.info_price .txt_num').text
    book_list.append(Book(i+1, title, author, price))

for book in book_list:
    print(book)

