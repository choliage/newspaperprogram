from scraper_udn import fetch_udn_articles_and_save
from scraper_ct import fetch_ct_articles_and_save

if __name__ == "__main__":
    fetch_udn_articles_and_save(
        page_url="https://udn.com/news/cate/2/7225",
        source_label="聯合國際",
        output_dir=r"C:\Users\lolee\Desktop\studios\爬蟲\整合結果"
    )
    fetch_udn_articles_and_save(
        page_url="https://udn.com/news/cate/2/6644",
        source_label="聯合產經",
        output_dir=r"C:\Users\lolee\Desktop\studios\爬蟲\整合結果"
    )
    fetch_ct_articles_and_save(
        index_url="https://www.chinatimes.com/money/?chdtv",
        source_label="中時",
        output_dir=r"C:\Users\lolee\Desktop\studios\爬蟲\整合結果"
    )