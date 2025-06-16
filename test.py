import requests
from bs4 import BeautifulSoup
from newspaper import Article

#註:這是原本手寫的第一個版本
url = "https://udn.com/news/cate/2/7225"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.content, 'lxml')

output_path = r"C:\Users\lolee\Desktop\studios\爬蟲\爬出來的好料.txt"

dist = []

with open(output_path, "w", encoding="utf-8") as txt:
    count = 0
    for story in soup.find_all('div', class_='story-list__news'):
        h2 = story.find('h2')
        if h2:
            a = h2.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                link = "https://udn.com" + a['href']
                dist.append(link)

                print(f"{count+1}. 標題: {title}")
                print(f"   連結: {link}")
                print("-" * 40)

                txt.write(f"{count+1}. 標題: {title}\n")
                txt.write(f"   連結: {link}\n")
                txt.write("-" * 40 + "\n")
                count += 1

    print(f"\n總共抓到 {count} 則新聞\n")
    txt.write(f"\n總共抓到 {count} 則新聞\n\n")

    for i, url in enumerate(dist, 1):
        try:
            article = Article(url, language='zh')
            article.download()
            article.parse()

            print(f"第 {i} 篇文章內容：")
            print(article.text+ "\n") 
            print("=" * 40)

            txt.write(f"第 {i} 篇文章內容：\n")
            txt.write(article.text + "\n")
            txt.write("=" * 40 + "\n\n")

        except Exception as e:
            print(f" 第 {i} 篇失敗: {url}")
            print(f"原因: {e}\n")
            txt.write(f" 第 {i} 篇失敗: {url}\n")
            txt.write(f"原因: {e}\n\n")