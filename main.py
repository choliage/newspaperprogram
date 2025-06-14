import os
import time
from datetime import datetime
from scraper_udn import fetch_udn_articles_and_save
from scraper_ct import fetch_ct_articles_and_save
from datetime import datetime, timedelta
from scraper_ltn import fetch_ltn_articles_and_save

BASE_DIR = r"C:\Users\lolee\Desktop\studios\爬蟲\整合結果"

TARGETS = [
    {
        'label': '聯合國際',
        'url': 'https://udn.com/news/cate/2/7225',
        'fetch_and_save': fetch_udn_articles_and_save,
        'param_name': 'page_url'
    },
    {
        'label': '聯合產經',
        'url': 'https://udn.com/news/cate/2/6644',
        'fetch_and_save': fetch_udn_articles_and_save,
        'param_name': 'page_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=1&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=2&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=3&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=4&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=5&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=6&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=7&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '中時',
        'url': 'https://www.chinatimes.com/money/total?page=8&chdtv',
        'fetch_and_save': fetch_ct_articles_and_save,
        'param_name': 'index_url'
    },
     
    {
    'label': '自由時報',
    'url': 'https://ec.ltn.com.tw/',
    'fetch_and_save': fetch_ltn_articles_and_save,
    'param_name': 'index_url'
    }


]

def scan_once():
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 開始擷取")
    for target in TARGETS:
        print(f"📡 擷取：{target['label']}")
        try:
            kwargs = {
                target['param_name']: target['url'],
                'source_label': target['label'],
                'output_dir': BASE_DIR
            }
            target['fetch_and_save'](**kwargs)
        except Exception as e:
            print(f"❌ 擷取失敗：{target['label']}，原因：{e}")
    print("✅ 擷取完成\n")

if __name__ == "__main__":
    print("🔁 每小時新聞自動擷取啟動中...")
    while True:
        TimeHr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        now = datetime.now()
        next_hour = now + timedelta(hours=1)
        TimeHr2 = next_hour.strftime('%Y-%m-%d %H:%M:%S')
        scan_once()
        print("🕐 等待下一輪（1 小時）...\n")
        print("　　本次掃描結束時間",TimeHr)
        print("　　下次掃描結束時間",TimeHr2)
        time.sleep(3600)
