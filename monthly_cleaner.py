import os
from pathlib import Path
import shutil
import zipfile
import logging
from datetime import datetime, timedelta

def archive_last_month():
    try:
        base_path = Path(__file__).resolve().parent
    except NameError:
        base_path = Path(os.getcwd())

    base_dir = base_path / "整合結果"
    output_dir = base_dir / "monthly_archives"
    output_dir.mkdir(exist_ok=True)

    today = datetime.today()
    first_day_of_this_month = today.replace(day=1)
    last_month = first_day_of_this_month - timedelta(days=1)
    last_month_str = last_month.strftime("%Y-%m")

    zip_output = output_dir / f"{last_month_str}.zip"
    files_to_archive = []

    for category_folder in base_dir.iterdir():
        if category_folder.is_dir():
            for file in category_folder.glob("*.txt"):
                if file.name.startswith(last_month_str):
                    files_to_archive.append(file)

    if files_to_archive:
        with zipfile.ZipFile(zip_output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for file in files_to_archive:
                arcname = file.relative_to(base_dir)
                zf.write(file, arcname)
        for file in files_to_archive:
            file.unlink()
        logging.info(f"✔ 成功打包並刪除 {len(files_to_archive)} 個檔案 ➜ {zip_output}")
    else:
        logging.warning(f"✘ 沒有找到任何 {last_month_str} 的檔案可以壓縮")

if __name__ == "__main__":
    archive_last_month()