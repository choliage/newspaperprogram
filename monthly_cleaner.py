import os
from pathlib import Path
import zipfile
import logging
from datetime import datetime, timedelta

def archive_last_month():
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    base_dir = base_path / "整合結果"
    output_dir = base_dir / "monthly_archives"
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.today()
    first_day_of_this_month = today.replace(day=1)
    last_month = first_day_of_this_month - timedelta(days=1)
    last_month_str = last_month.strftime("%Y-%m")

    zip_output = output_dir / f"{last_month_str}.zip"
    files_to_archive = []

    # 收集所有 .txt 檔案
    if base_dir.exists():
        for category_folder in base_dir.iterdir():
            if category_folder.is_dir() and category_folder.name != "monthly_archives":
                for file in category_folder.glob("*.txt"):
                    if file.name.startswith(last_month_str):
                        files_to_archive.append(file)

    if not files_to_archive:
        msg = f"✘ 沒有找到任何 {last_month_str} 的檔案可以壓縮"
        print(msg)
        logging.warning(msg)
        return

    # 讀取 zip 中已存在的檔案清單
    existing_files = set()
    if zip_output.exists():
        with zipfile.ZipFile(zip_output, 'r') as zf:
            existing_files = set(zf.namelist())

    new_files_count = 0
    added_files = []

    # 新增進 zip，避免重複
    with zipfile.ZipFile(zip_output, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files_to_archive:
            arcname = file.relative_to(base_dir)
            if str(arcname) not in existing_files:
                zf.write(file, arcname)
                file.unlink()
                added_files.append(str(arcname))
                new_files_count += 1

    # 顯示訊息
    if new_files_count > 0:
        print(f"📦 新增以下檔案到 {zip_output.name}:")
        for name in added_files:
            print(f"  └─ {name}")
        print(f"✔ 共新增 {new_files_count} 個檔案並從硬碟刪除")
        logging.info(f"✔ 新增 {new_files_count} 檔案 ➜ {zip_output}")
    else:
        print(f"✓ 沒有新檔案需要新增，{zip_output.name} 已是最新狀態")
        logging.info(f"✓ zip 無須更新：{zip_output}")

if __name__ == "__main__":
    archive_last_month()
