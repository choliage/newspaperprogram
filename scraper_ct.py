import os
import logging
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from newspaper import Article

TRUSTED_DOMAINS = [
    "www.chinatimes.com", "m.chinatimes.com",
    "opinion.chinatimes.com", "news.chinatimes.com"
]

def load_done_urls(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def append_done_url(file_path, url):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def load_done_urls(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def append_done_url(file_path, url):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")
def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("window-size=1200x800")
    options.add_argument("user-agent=Mozilla/5.0")
    return webdriver.Chrome(options=options)

def sanitize_filename(title):
    return re.sub(r'[\\/:*?"<>|]', "_", title)[:50]


from urllib.parse import urlparse

def normalize_url(url):
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.replace('www.', '').lower()
        path = parsed.path.rstrip('/')
        query = f"?{parsed.query}" if parsed.query else ''
        return f"{netloc}{path}{query}"
    except:
        return url.strip().lower()


def fetch_ct_articles_and_save(index_url, output_dir, source_label="中時"):
    subdir = os.path.join(output_dir, source_label)
    done_file = os.path.join(subdir, "done_urls.txt")
    done_urls = load_done_urls(done_file)
    normalized_done_urls = set(normalize_url(url) for url in done_urls)
    os.makedirs(subdir, exist_ok=True)

    driver = create_driver()
    driver.get(index_url)
    time.sleep(6)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()

    stories = soup.find_all('div', class_='cropper')
    logging.info(f"🔍 [中時] 找到 {len(stories)} 則文章")

    for i, story in enumerate(stories, 1):
        
        a = story.find('a')
        if not a or not a.get('href'):
            continue

        raw_link = a['href'].strip()

        full_url = "https://www.chinatimes.com" + raw_link if raw_link.startswith("/") else raw_link
        
        if normalize_url(full_url) in normalized_done_urls or normalize_url(a['href'].strip()) in normalized_done_urls:
            logging.info(f"   ⏩ 已處理過（URL 重複或跳轉網址）")
            continue

        domain = urlparse(full_url).netloc
        if not any(domain.endswith(td) for td in TRUSTED_DOMAINS):
            continue

        title = a.get('title', '').strip() or a.text.strip()
        logging.info(f"  {i:02d}. 嘗試擷取文章：{title}")

        try:
            driver = create_driver()
            driver.get(full_url)
            time.sleep(5)
            html = driver.page_source
            driver.quit()

            
            article = Article(full_url, language='zh')
            article.set_html(html)
            article.parse()

            publish_time = article.publish_date.strftime("%Y-%m-%d_%H%M") if article.publish_date else datetime.now().strftime("%Y-%m-%d_%H%M")
            clean_title = sanitize_filename(article.title or title)
            filename = f"{publish_time}_{source_label}_{clean_title}.txt"
            filepath = os.path.join(subdir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"標題: {article.title or title}\n")
                f.write(f"連結: {full_url}\n\n")
                f.write(article.text)
            
            append_done_url(done_file, full_url)

            logging.info(f"   ✅ 已儲存：{filename}")
        except Exception as e:
            logging.error(f"   ❌ 擷取失敗：{e}")


def fetch_ct_articles_auto(index_url, output_dir, source_label="中時", max_pages=5):
    logging.info(f"🌀 自動擷取中時頁面：從 {index_url} 開始，最多 {max_pages} 頁")

    base_url = "https://www.chinatimes.com/money/total?page="
    subdir = os.path.join(output_dir, source_label)
    os.makedirs(subdir, exist_ok=True)
    done_file = os.path.join(subdir, "done_urls.txt")
    done_urls = load_done_urls(done_file)
    normalized_done_urls = set(normalize_url(url) for url in done_urls)

    for page in range(1, max_pages + 1):
        url = f"{base_url}{page}&chdtv"
        logging.info(f"📄 掃描中時第 {page} 頁：{url}")

        driver = create_driver()
        driver.get(url)
        time.sleep(6)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit()

        # 先抓有圖的文章
        stories = soup.find_all('div', class_='cropper')
        all_links = soup.find_all('a', href=True)  # ⭐ 擴增：抓全部連結

        logging.info(f"🔍 找到 {len(stories)} 則圖片文章，{len(all_links)} 條連結")

        story_links = set()
        for story in stories:
            a = story.find('a')
            if a and a.get('href'):
                story_links.add(a['href'].strip())

        def handle_story(full_url, title, is_extra=False):
            try:
                driver = create_driver()
                driver.get(full_url)
                time.sleep(5)
                html = driver.page_source
                driver.quit()

                article = Article(full_url, language='zh')
                article.set_html(html)
                article.parse()

                publish_time = article.publish_date.strftime("%Y-%m-%d_%H%M") if article.publish_date else datetime.now().strftime("%Y-%m-%d_%H%M")
                clean_title = sanitize_filename(article.title or title)
                filename = f"{publish_time}_{source_label}_{clean_title}.txt"
                filepath = os.path.join(subdir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"標題: {article.title or title}")

                    f.write(f"連結: {full_url}")


                    f.write(article.text)

                append_done_url(done_file, full_url)
                normalized_done_urls.add(normalize_url(full_url))

                tag = "🖼 圖文" if not is_extra else "📄 無圖"
                logging.info(f"   ✅ 已儲存（{tag}）：{filename}")
                return True
            except Exception as e:
                logging.error(f"   ❌ 擷取失敗：{e}")
                return False

        new_count = 0

        # 圖文文章處理
        for i, story in enumerate(stories, 1):
            a = story.find('a')
            if not a or not a.get('href'):
                continue
            raw_link = a['href'].strip()
            full_url = "https://www.chinatimes.com" + raw_link if raw_link.startswith("/") else raw_link
            if normalize_url(full_url) in normalized_done_urls:
                continue
            domain = urlparse(full_url).netloc
            if not any(domain.endswith(td) for td in TRUSTED_DOMAINS):
                continue
            title = a.get('title', '').strip() or a.text.strip()
            if handle_story(full_url, title):
                new_count += 1

        # ⭐ 補漏：無圖文章處理
        for a in all_links:
            
            href = a.get('href', '').strip()
            if not href or href in story_links:
                continue
            if not href.startswith('/'):
                continue
            full_url = "https://www.chinatimes.com" + href
            if normalize_url(full_url) in normalized_done_urls:
                continue
            domain = urlparse(full_url).netloc
            if not any(domain.endswith(td) for td in TRUSTED_DOMAINS):
                continue
            if not re.match(r"^/news/|^/realtimenews/", href):
                continue
            if "/video/" in href or "/tag/" in href or "/app/" in href:
                continue

            # 標題要夠長才處理
            title = a.get('title', '').strip() or a.text.strip()
            if len(title) < 5 or "影音" in title or "APP" in title:
                continue
            title = a.get('title', '').strip() or a.text.strip()
            if title and len(title) >= 5 and "影音專區" not in title:
                if handle_story(full_url, title, is_extra=True):
                    new_count += 1

        if new_count == 0:
            logging.warning(f"⚠️ 無新文章，提早結束中時擷取")
            break
