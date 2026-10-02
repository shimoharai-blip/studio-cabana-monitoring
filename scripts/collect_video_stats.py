import os
import sys
import json
import logging
import pandas as pd

from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build

# ==========================================
# 設定
# ==========================================

CSV_PATH = "data/video_daily_stats.csv"
LOG_PATH = "logs/monitor.log"

JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST).strftime("%Y-%m-%d")

# ==========================================
# ディレクトリ作成
# ==========================================

os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# ==========================================
# ログローテーション
# ==========================================

if os.path.exists(LOG_PATH):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) > 10000:
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines[-5000:])

    except Exception:
        pass

# ==========================================
# Logging
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# ==========================================
# Main
# ==========================================

def main():

    logger.info("=" * 50)
    logger.info("Monitoring Start")

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise ValueError
