import requests
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import os
import re
import time

headers = {'User-Agent': 'Mozilla/5.0'}

# ✅ JS 跳轉解析：用 Selenium 模擬
def get_final_url_js(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--use-gl=swiftshader")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(5)
        return driver.current_url
    except Exception as e:
        print(f"⚠️ Selenium 跳轉失敗: {e}")
        return url
    finally:
        driver.quit()

# ✅ 通用跳轉處理：requests → meta → JS
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

# ✅ 擷取頁面新聞列表
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

# ✅ 檔名清洗（避免非法字元）
def sanitize_filename(title):
    return re.sub(r'[\\/:*?"<>|]', "", title)[:50]

# ✅ 主爬蟲：每篇寫入單一檔案
def scrape_udn(page_url, output_dir, prefix="udn"):
    links = get_udn_links(page_url)
    os.makedirs(output_dir, exist_ok=True)

    for i, item in enumerate(links, 1):
        orig_url = item['url']
        final_url = get_final_url(orig_url)

        try:
            article = Article(final_url, language='zh')
            article.download()
            article.parse()

            clean_title = sanitize_filename(item['title'])
            filename = f"{prefix}_{i:03}_{clean_title}.txt"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"標題: {item['title']}\n")
                f.write(f"連結: {final_url}\n\n")
                f.write(article.text)

            print(f"✅ 寫入: {filename}")
        except Exception as e:
            print(f"❌ 第 {i} 篇抓取失敗：{e}")

# ✅ 主程式：可切換不同分類頁
if __name__ == "__main__":
    scrape_udn(
        page_url="https://udn.com/news/cate/2/7225",  # 國際新聞
        output_dir=r"C:\Users\lolee\Desktop\studios\爬蟲\國際",
        prefix="udn7225"
    )
    scrape_udn(
        page_url="https://udn.com/news/cate/2/6644",  
        output_dir=r"C:\Users\lolee\Desktop\studios\爬蟲\產經",
        prefix="udn6644"
    )