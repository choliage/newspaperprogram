import requests
from bs4 import BeautifulSoup

reqget = requests.get("https://udn.com/news/cate/2/7225")
print(reqget.text)