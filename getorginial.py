import requests
from bs4 import BeautifulSoup

reqget = requests.get("https://www.chinatimes.com/money/?chdtv")
print(reqget.text)