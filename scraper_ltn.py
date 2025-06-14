
import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from newspaper import Article

def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("window-size=1200x800")
    options.add_argument("user-agent=Mozilla/5.0")
    return webdriver.Chrome(options=options)

def sanitize_filename(title):
    return re.sub(r'[\\/:*?"<>|]', "_", title)[:50]

def normalize_url(url):
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.replace("www.", "").lower()
        path = parsed.path.rstrip("/")
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{netloc}{path}{query}"
    except:
        return url.strip().lower()

def is_valid_news_url(url):
    parsed = urlparse(url)
    return (
        "ec.ltn.com.tw" in parsed.netloc and
        parsed.path.startswith("/article/") and
        not parsed.netloc.startswith("market.") and
        "/video/" not in parsed.path
    )

def load_done_urls(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def append_done_url(file_path, url):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(url + "\n")


# 模擬下滑直到頁面長度穩定，確保第二頁載入
def scroll_to_bottom(driver, wait_time=2, max_tries=1):
    last_height = driver.execute_script("return document.body.scrollHeight")
    tries = 0
    while tries < max_tries:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        tries += 1

def fetch_ltn_articles_and_save(index_url, output_dir, source_label="自由時報"):
    subdir = os.path.join(output_dir, source_label)
    done_file = os.path.join(subdir, "done_urls.txt")
    done_urls = load_done_urls(done_file)
    normalized_done_urls = set(normalize_url(url) for url in done_urls)
    os.makedirs(subdir, exist_ok=True)

    driver = create_driver()
    driver.get(index_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    category_blocks = soup.select("article.boxTitle, div.halfBox.boxTitle")
    total_articles = 0

    for block in category_blocks:
        if "影音專區" in block.get("data-desc", ""):
            print("🔕 跳過影音專區")
            continue

        cat_a = block.find("a", class_="sortitle")
        if not cat_a or "/video/" in cat_a.get("href", ""):
            continue  # 忽略影音分類

        cat_url = urljoin(index_url, cat_a["href"])
        cat_title = cat_a.get("title", "未命名分類").strip()
        print(f"📂 分類：《{cat_title}》")

        driver = create_driver()
        driver.get(cat_url)
        scroll_to_bottom(driver)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

        anchors = soup.select("a.news1.boxText, a.boxText")

        for li in soup.select("li[data-page]"):
            a = li.find("a", href=True)
            if a and "ec.ltn.com.tw/article/" in a["href"]:
                anchors.append(a)

        # 過濾非新聞連結
        anchors = [a for a in anchors if is_valid_news_url(urljoin(cat_url, a["href"]))]
        print(f"  🔎 共找到 {len(anchors)} 篇文章")

        for i, a in enumerate(anchors, 1):
            href = a["href"].strip()
            full_url = urljoin(cat_url, href)
            norm_url = normalize_url(full_url)
            if norm_url in normalized_done_urls:
                print(f"   ⏩ 已處理過：{full_url}")
                continue

            print(f"   {i:02d}. 擷取文章：{full_url}")
            try:
                driver = create_driver()
                driver.get(full_url)
                time.sleep(4)
                html = driver.page_source
                driver.quit()

                article = Article(full_url, language="zh")
                article.set_html(html)
                article.parse()

                publish_time = article.publish_date.strftime("%Y-%m-%d_%H%M") if article.publish_date else datetime.now().strftime("%Y-%m-%d_%H%M")
                clean_title = sanitize_filename(article.title or a.get("title", "未命名"))
                filename = f"{publish_time}_{source_label}_{clean_title}.txt"
                filepath = os.path.join(subdir, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"分類: {cat_title}\n")
                    f.write(f"標題: {article.title}\n")
                    f.write(f"連結: {full_url}\n\n")
                    f.write(article.text)

                append_done_url(done_file, full_url)
                print(f"   ✅ 儲存成功：{filename}")

                total_articles += 1

            except Exception as e:
                print(f"   ❌ 擷取失敗：{e}")

    print(f"✅ 完成，自由時報共儲存 {total_articles} 篇文章")
