import requests
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import time

headers = {'User-Agent': 'Mozilla/5.0'}

output_path = r"C:\Users\lolee\Desktop\studios\爬蟲\爬出來的好料.txt"


def get_final_url_js(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--use-gl=swiftshader")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(5)
        return driver.current_url
    except Exception as e:
        print(f"❌ Selenium 跳轉失敗：{e}")
        return url
    finally:
        driver.quit()

def get_final_url(original_url):
    try:
        res = requests.get(original_url, headers=headers, timeout=10, allow_redirects=True)
        soup = BeautifulSoup(res.text, "lxml")

        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta and "content" in meta.attrs:
            content = meta["content"]
            if "url=" in content.lower():
                refresh_url = content.split("url=")[-1].strip()
                return urljoin(original_url, refresh_url)

        final_url = res.url
        if "udn.com/news/story" in final_url:
            return get_final_url_js(original_url)
        return final_url

    except:
        return get_final_url_js(original_url)

def get_udn_links(page_url):
    res = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(res.content, 'lxml')
    links = []

    for story in soup.find_all('div', class_='story-list__news'):
        h2 = story.find('h2')
        if h2:
            a = h2.find('a')
            if a and a.get('href'):
                title = a.text.strip()
                link = "https://udn.com" + a['href']
                links.append({'title': title, 'url': link})
    return links


def scrape_udn(page_url, output_path):
    links = get_udn_links(page_url)

    with open(output_path, "w", encoding="utf-8") as txt:
        txt.write(f"總共抓到 {len(links)} 則新聞\n\n")

        for i, item in enumerate(links, 1):
            orig_url = item['url']
            final_url = get_final_url(orig_url)

            try:
                article = Article(final_url, language='zh')
                article.download()
                article.parse()

                txt.write(f"{i}. 標題: {item['title']}\n")
                txt.write(f"連結: {final_url}\n")
                txt.write(article.text + "\n\n")
            except Exception as e:
                txt.write(f"{i}. 標題: {item['title']}\n")
                txt.write(f"連結: {final_url}\n")
                txt.write(f"抓取失敗: {e}\n\n")


if __name__ == "__main__":
    scrape_udn(
        page_url="https://udn.com/news/cate/2/7225",
        output_path=r"C:\Users\lolee\Desktop\studios\爬蟲\好料_國際.txt"
    )
    scrape_udn(
        page_url="https://udn.com/news/cate/2/6644",
        output_path=r"C:\Users\lolee\Desktop\studios\爬蟲\好料_產經.txt"
    )