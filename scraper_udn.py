import os
import logging
import re
import requests
import time
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def load_done_urls(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def normalize_url(url):

    parsed = re.sub(r'^https?://(www\.)?', '', url).rstrip('/')
    return parsed.lower()

def append_done_url(file_path, url):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def get_final_url_js(url):
    logging.info(f"🌐 使用 Selenium 嘗試跳轉: {url}")
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--use-gl=swiftshader")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(5)
        return driver.current_url
    except Exception as e:
        logging.warning(f"⚠️ Selenium 失敗: {e}")
        return url
    finally:
        driver.quit()

def get_final_url(original_url):
    logging.info(f"🔗 嘗試解析跳轉網址: {original_url}")
    try:
        res = requests.get(original_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")
        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta and "content" in meta.attrs:
            content = meta["content"]
            if "url=" in content.lower():
                refresh_url = content.split("url=")[-1].strip()
                return urljoin(original_url, refresh_url)
        if "udn.com/news/story" in res.url:
            return get_final_url_js(original_url)
        return res.url
    except Exception as e:
        logging.error(f"❌ requests 跳轉失敗: {e}")
        return get_final_url_js(original_url)

def sanitize_filename(title):
    return re.sub(r'[\\/:*?"<>|]', "_", title)[:50]

def fetch_udn_articles_and_save(page_url, output_dir, source_label="聯合"):
    logging.info(f"🚩 進入 fetch_udn_articles_and_save：{page_url}")
    subdir = os.path.join(output_dir, source_label)
    done_file = os.path.join(subdir, "done_urls.txt")
    done_urls = load_done_urls(done_file)
    os.makedirs(subdir, exist_ok=True)
  
    try:
        res = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.content, 'lxml')
        blocks = soup.find_all('div', class_='story-list__news')
        logging.info(f"🔍 找到 {len(blocks)} 篇文章區塊")
        

        for i, story in enumerate(blocks, 1):
            h2 = story.find('h2')
            if not h2:
                continue
            a = h2.find('a')
            if not a or not a.get('href'):
                continue

            title = a.text.strip()
            link = "https://udn.com" + a['href']


            if link in done_urls:
                logging.info(f"   ⏩ 預檢：已處理過（URL 重複），完全略過")
                continue


            final_url = get_final_url(link)

            logging.info(f"  {i:02d}. 嘗試擷取文章：{title}")
            try:
                article = Article(final_url, language='zh')
                article.download()
                article.parse()
                if len(article.text.strip()) < 30:
                    logging.info("   ⚠️ 內容過短，略過")
                    continue

                publish_time = article.publish_date.strftime("%Y-%m-%d_%H%M") if article.publish_date else datetime.now().strftime("%Y-%m-%d_%H%M")
                clean_title = sanitize_filename(article.title or title)
                filename = f"{publish_time}_{source_label}_{clean_title}.txt"
                filepath = os.path.join(subdir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"標題: {article.title}\n")
                    f.write(f"連結: {final_url}\n\n")
                    f.write(article.text)
                append_done_url(done_file, link)   

                logging.info(f"   ✅ 已儲存：{filename}")
            except Exception as e:
                logging.error(f"   ❌ 擷取失敗: {e}")

    except Exception as outer_e:
        logging.error(f"❌ 無法解析主頁面：{outer_e}")
