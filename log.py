import logging
from datetime import datetime
from pathlib import Path

class GuiLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)

            def write():
                self.text_widget.insert("end", msg + "\n")
                self.text_widget.see("end")

            self.text_widget.after(0, write)
        except Exception:
            self.handleError(record)

def setup_logging_with_gui(text_widget):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now():%Y-%m-%d}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # 清掉已存在 handler（避免重複）
    root_logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # GUI handler
    gh = GuiLogHandler(text_widget)
    gh.setFormatter(formatter)
    root_logger.addHandler(gh)

    logging.info(f"📓 運行日誌的起點 : {datetime.now():%Y-%m-%d_%H:%M}")
    logging.info(f"="*40)