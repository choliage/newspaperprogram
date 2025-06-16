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
from log import setup_logging_with_gui, GuiLogHandler
from scraper_udn import fetch_udn_articles_and_save
from scraper_ltn import fetch_ltn_articles_and_save, fetch_ltn_world_articles_and_save
from scraper_ct import fetch_ct_articles_auto
from checkEPU import run_check
from datetime import datetime, timedelta
from monthly_cleaner import archive_last_month

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
    
    run_once_button2 = ctk.CTkButton(
    button_frame,
    text="▶ EPU重算",
    command=lambda: run_check(BASE_DIR)
    )
    run_once_button2.pack(side="left", padx=(10))

    run_once_button3 = ctk.CTkButton(
        button_frame,
        text="▶ EXCEL統計資料",
        command=lambda: postprocess_to_excel(BASE_DIR)
    )
    run_once_button3.pack(side="left", padx=(10,10))

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
            
            update_status("等待中", "🟡")
            time.sleep((next_run - datetime.now()).total_seconds())
            

    threading.Thread(target=background_task, daemon=True).start()
    update_countdown_loop()
    app.mainloop()