import requests
from bs4 import BeautifulSoup

reqget = requests.get("https://ec.ltn.com.tw/")
print(reqget.text)