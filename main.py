import os
import time
import pandas as pd
import re
import random
import logging
import customtkinter as ctk
import io
import sys
import threading
import subprocess
from log import setup_logging_with_gui
from scraper_udn import fetch_udn_articles_and_save
from scraper_ltn import fetch_ltn_articles_and_save, fetch_ltn_world_articles_and_save
from scraper_ct import fetch_ct_articles_auto
from checkEPU import run_check, generate_epu_index_report
from datetime import datetime, timedelta
from monthly_cleaner import archive_last_month
from pathlib import Path


is_animating = False

BASE_DIR = os.path.join(os.path.abspath(os.getcwd()), "整合結果")

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
        'fetch_and_save': fetch_ct_articles_auto,
        'param_name': 'index_url'
    },
    {
        'label': '自由時報_財經',
        'url': 'https://ec.ltn.com.tw/',
        'fetch_and_save': fetch_ltn_articles_and_save,
        'param_name': 'index_url'
    },
    {
        'label': '自由時報_國際',
        'url': 'https://news.ltn.com.tw/list/breakingnews/world',
        'fetch_and_save': fetch_ltn_world_articles_and_save,
        'param_name': 'index_url'
    }


]

def set_default_font():
    from tkinter import font as tkfont
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family="Microsoft JhengHei UI", size=13)

def animate_status_label(base_text="掃描中", icon="🔴"):
    def run():
        dots = [".", ". .", ". . ."]
        i = 0
        while is_animating:
            status_label.configure(text=f"{icon} 狀態：{base_text}{dots[i % len(dots)]}")
            i += 1
            time.sleep(0.5)
    threading.Thread(target=run, daemon=True).start()    

def update_countdown_loop():
    def loop():
        while True:
            if hasattr(app, "next_run_time"):
                remaining = app.next_run_time - datetime.now()
                if remaining.total_seconds() > 0:
                    mins, secs = divmod(int(remaining.total_seconds()), 60)
                    countdown_label.configure(text=f"⏳ 下次擷取剩餘：{mins} 分 {secs} 秒")
                else:
                    countdown_label.configure(text=f"⏳ 正在擷取中...")
            else:
                countdown_label.configure(text="⏳ 下次擷取剩餘：-- 分 -- 秒")
            time.sleep(1)
    threading.Thread(target=loop, daemon=True).start()

def scan_once():
    logging.info(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 開始擷取")
    logging.info("📁 儲存資料夾：%s", BASE_DIR)
    for target in TARGETS:
        logging.info(f"📡 擷取：{target['label']}")
        try:
            kwargs = {
                target['param_name']: target['url'],
                'source_label': target['label'],
                'output_dir': BASE_DIR
            }
            target['fetch_and_save'](**kwargs)
        except Exception as e:
            logging.error(f"❌ 擷取失敗：{target['label']}，原因：{e}")
    logging.info(f"✅ 擷取完成\n")
    # 🔽 自動產出 Excel：每週為單位彙整新聞標題、日期、網址

def open_result_folder():
    subprocess.Popen(['explorer', BASE_DIR])

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

            logging.info(f"📊 {source} 匯出 Excel 完成（共 {len(by_week)} 週）")

def summarize_run(base_dir):
    from pathlib import Path
    import pandas as pd
    import re

    target_date = datetime.now().strftime("%Y-%m-%d")
    base = Path(base_dir)

    txt_report = {}
    grouped_sources = {}
    excel_report = {}

    # 映射設定：將子來源歸入主報社名稱
    source_mapping = {
        "聯合國際": "聯合報",
        "聯合產經": "聯合報",
        "自由時報_國際": "自由時報",
        "自由時報_財經": "自由時報",
        "中時": "中時"
    }

    # 第一步：掃描各子來源 txt
    for folder in base.iterdir():
        if not folder.is_dir() or folder.name == "EPU匯出結果":
            continue
        matched_txts = list(folder.glob(f"*{target_date}*.txt"))
        if matched_txts:
            name = folder.name
            mapped = source_mapping.get(name, name)
            count = len(matched_txts)
            txt_report[name] = count
            if mapped not in grouped_sources:
                grouped_sources[mapped] = []
            grouped_sources[mapped].append(name)

    # 第二步：讀取 Excel
    epu_excel_dir = base / "EPU匯出結果" / target_date
    if not epu_excel_dir.exists():
        logging.warning("⚠ 無法找到當日 EPU 匯出 Excel 資料夾")
        return

    for file in epu_excel_dir.glob("*_EPU檢查結果.xlsx"):
        try:
            df = pd.read_excel(file)
            df_valid = df[df["檔名"].notna()]
            count = len(df_valid)
            match = (df_valid["是否符合 EPU"] == "✔ 是").sum()
            name_match = re.match(rf"{target_date}_(.+?)_EPU檢查結果", file.stem)
            if name_match:
                src_label = name_match.group(1)
                excel_report[src_label] = {"excel_count": count, "epu_count": match}
        except Exception as e:
            logging.warning(f"⚠ 讀取 Excel 檔失敗：{file.name} - {e}")

    # 顯示
    logging.info("\n📋【擷取總結報告】")
    logging.info(f"📅 日期：{target_date}")
    logging.info(f"📰 掃描來源：{', '.join(sorted(txt_report))}")

    total_txt = 0
    total_excel = 0
    total_epu = 0

    for main_src in sorted(grouped_sources):
        children = grouped_sources[main_src]
        txt_sum = sum(txt_report.get(c, 0) for c in children)
        total_txt += txt_sum

        # 顯示主來源 Excel 數據（如果有）
        if main_src in excel_report:
            excel_count = excel_report[main_src]["excel_count"]
            epu_count = excel_report[main_src]["epu_count"]
            total_excel += excel_count
            total_epu += epu_count
            logging.info(f"\n   └ {main_src}：Excel實際處理 {excel_count}，符合 EPU：{epu_count}")
        else:
            logging.info(f"\n   └ {main_src}：Excel實際處理 0，符合 EPU：0")

        for child in children:
            logging.info(f"       └ {child}：txt原始數 {txt_report.get(child, 0)}")

    # 顯示指數
    epu_index_value = "-"
    index_path = base / "EPU匯出結果" / "EPU_每日指數.xlsx"
    if index_path.exists():
        try:
            df_idx = pd.read_excel(index_path)
            today_row = df_idx[df_idx["日期"] == target_date]
            if not today_row.empty:
                epu_index_value = round(float(today_row.iloc[0]["正規化指數"]), 2)
        except:
            pass

    logging.info(f"\n📦 今日 txt 總數：{total_txt} 篇")
    logging.info(f"📄 Excel 實際處理數：{total_excel} 篇，符合 EPU：{total_epu} 篇")
    logging.info(f"📈 今日 EPU 指數：{epu_index_value}")



if __name__ == "__main__":
  

    # GUI 介面設定
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    set_default_font()
    button_frame = ctk.CTkFrame(app)
    button_frame.pack(side="bottom", fill="x", pady=(10, 10))
    
    

    def run_once_now():
        def task():
            global is_animating
            is_animating = True
            animate_status_label("掃描中", "🔴")
            logging.info(f"🧨【手動觸發】開始於：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            scan_once()
            is_animating = False
            update_status("完成", "🟢")
            logging.info(f"✅ 掃描完成：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        threading.Thread(target=task).start()

    run_once_button = ctk.CTkButton(button_frame, text="▶ 立即重新執行爬蟲", command=run_once_now)
    run_once_button.pack(side="left", padx=(10))
    

    run_once_button3 = ctk.CTkButton(
        button_frame,
        text="▶ EXCEL統計資料",
        command=lambda: postprocess_to_excel(BASE_DIR)
    )
    run_once_button3.pack(side="left", padx=(10,10))
    run_summary_button = ctk.CTkButton(
        button_frame,
        text="▶ 重新統計摘要",
        command=lambda: summarize_run(BASE_DIR)
    )
    run_summary_button.pack(side="left", padx=(10))
    open_button = ctk.CTkButton(button_frame, text="📂 開啟整合資料夾", command=open_result_folder)
    open_button.pack(side="right",padx=(10,10))

    app.geometry("800x500")
    app.title("P.O.E - Precision,Observe,Exact. Ver.1.0.0")

    # 狀態燈 + 標籤區
    status_label = ctk.CTkLabel(app, text="🟡 狀態：等待中", font=("Segoe UI", 16))
    status_label.pack(pady=(15, 5))

    countdown_label = ctk.CTkLabel(app, text="⏳ 下次擷取剩餘：-- 分 -- 秒", font=("Segoe UI", 14))
    countdown_label.pack(pady=(0, 5))

    # 日誌區
    log_box = ctk.CTkTextbox(app, wrap="word")
    log_box.pack(padx=20, pady=(0, 20), fill="both", expand=True)

    setup_logging_with_gui(log_box)

    # 將 stdout 導入 GUI
    class TextRedirector(io.TextIOBase):
        def write(self, s):
            log_box.insert("end", s)
            log_box.see("end")
            return len(s)
    sys.stdout = TextRedirector()
    sys.stderr = TextRedirector()

    # 狀態燈控制函數
    def update_status(text, emoji):
        status_label.configure(text=f"{emoji} 狀態：{text}")

    # 執行原始 while True
    def background_task():
        logging.info(f"🔁 每小時新聞自動擷取啟動中...") 
        while True:
            start_time = datetime.now()
            update_status("執行中", "🔴")
            logging.info(f"\n⏰ 本輪開始時間：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            global is_animating
            is_animating = True
            animate_status_label("掃描中", "🔴")
            scan_once()
            is_animating = False
            update_status("等待中", "🟡")
            end_time = datetime.now()
            next_run = end_time + timedelta(hours=1)
            app.next_run_time = next_run
            
            run_check(BASE_DIR) 
            generate_epu_index_report("整合結果")
            postprocess_to_excel(BASE_DIR)
            archive_last_month()
            logging.info(f"✅ 完成：{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"🕐 下次：{next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(random.choice([
                "🔹 P.O.E. 系統完美執行",
                "🔹 Precision. Observe. Exact. 已經完成了P.O.E.任務",
                "🔹 小提示:P.O.E.也是開發者最愛又最恨的遊戲縮寫",
                "🔹 已完成本輪，請至整合資料夾中確認輸出"
            ]))
            summarize_run(BASE_DIR)
            
            update_status("等待中", "🟡")
            time.sleep((next_run - datetime.now()).total_seconds())
            

    threading.Thread(target=background_task, daemon=True).start()
    update_countdown_loop()
    app.mainloop()