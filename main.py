import os
import time
from datetime import datetime
from scraper_udn import fetch_udn_articles_and_save
from scraper_ct import fetch_ct_articles_and_save
from datetime import datetime, timedelta
from scraper_ltn import fetch_ltn_articles_and_save
import pandas as pd
import re
import random

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
    'label': '自由時報',
    'url': 'https://ec.ltn.com.tw/',
    'fetch_and_save': fetch_ltn_articles_and_save,
    'param_name': 'index_url'
    }


]
    

def scan_once():
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 開始擷取")
    print(f"\n程序 💀ABSOLUTE-CINEMA💀 已經啟動")
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
    # 🔽 自動產出 Excel：每週為單位彙整新聞標題、日期、網址
    def postprocess_to_excel(output_root_dir):
        
        from datetime import datetime
        from collections import defaultdict

        def extract_info_from_txt(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            title_match = re.search(r"標題:\s*(.*)", content)
            url_match = re.search(r"連結:\s*(https?://[^\s]+)", content)
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})[_ ]?\d{0,4}", os.path.basename(filepath))
            return {
                "date": date_match.group(1) if date_match else None,
                "title": title_match.group(1).strip() if title_match else "無標題",
                "url": url_match.group(1).strip() if url_match else "無連結"
            }

        def group_by_week(data):
            grouped = defaultdict(list)
            for item in data:
                try:
                    date_obj = datetime.strptime(item["date"], "%Y-%m-%d")
                    year, week, _ = date_obj.isocalendar()
                    key = f"{year}_W{week:02d}"
                    grouped[key].append(item)
                except:
                    continue
            return grouped

        for source in os.listdir(output_root_dir):
            source_path = os.path.join(output_root_dir, source)
            if not os.path.isdir(source_path):
                continue

            all_items = []
            for fname in os.listdir(source_path):
                if fname.endswith(".txt"):
                    info = extract_info_from_txt(os.path.join(source_path, fname))
                    if info["date"]:
                        all_items.append(info)

            by_week = group_by_week(all_items)

            output_dir = os.path.join(source_path, "excel_by_week")
            os.makedirs(output_dir, exist_ok=True)

            for week_key, items in by_week.items():
                df = pd.DataFrame(items)[["date", "title", "url"]]
                df.sort_values("date", inplace=True)
                out_path = os.path.join(output_dir, f"{week_key}.xlsx")
                df.to_excel(out_path, index=False)

            print(f"📊 {source} 匯出 Excel 完成（共 {len(by_week)} 週）")

    postprocess_to_excel(BASE_DIR)

if __name__ == "__main__":
    print("🔁 每小時新聞自動擷取啟動中...")
    while True:
        start_time = datetime.now()
        print(f"\n⏰ 本輪開始時間：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        scan_once()

        end_time = datetime.now()
        next_run_time = end_time + timedelta(hours=1)
        sleep_seconds = (next_run_time - datetime.now()).total_seconds()

        print(f"✅ 本輪完成時間：{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 預計下一輪開始時間：{next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(random.choice([
            "跑都跑完了，先去喝個茶吧",
            "兄阿，居然成功了，絕對的電影院💀",
            "男人我罐頭我說 (Man what can I say)",
            "又跑一輪，凌晨四點叫 Kobe 把我載走好了"
        ]))

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)