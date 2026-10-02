
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

JSON_PATH = "videos.json"
CSV_PATH = "data/video_daily_stats.csv"
LOG_PATH = "logs/monitor.log"

JST = timezone(timedelta(hours=9))

NOW = datetime.now(JST)
TODAY = NOW.strftime("%Y-%m-%d %H:%M")

COLUMNS = [
    "date",
    "video_id",
    "title",
    "views",
    "likes",
    "comments",
    "views_gain",
    "likes_gain",
    "comments_gain",
    "views_growth_rate",
    "likes_growth_rate",
    "comments_growth_rate",
    "like_rate",
    "comment_rate",
    "engagement_rate"
]

# ==========================================
# ディレクトリ
# ==========================================

os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

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
# JSON読み込み
# ==========================================

def load_videos():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data["videos"]

    if not videos:
        raise ValueError("監視対象動画がありません")

    return videos

# ==========================================
# YouTube API
# ==========================================

def fetch_stats(youtube, videos):

    results = []

    for start in range(0, len(videos), 50):

        batch = videos[start:start + 50]

        ids = ",".join(
            v["video_id"] for v in batch
        )

        response = youtube.videos().list(
            part="snippet,statistics",
            id=ids
        ).execute()

        items = {
            item["id"]: item
            for item in response.get("items", [])
        }

        for video in batch:

            vid = video["video_id"]

            if vid not in items:
                logger.warning(f"取得できません: {vid}")
                continue

            item = items[vid]
            stats = item["statistics"]

            results.append({
                "date": TODAY,
                "video_id": vid,
                "title": item["snippet"]["title"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0))
            })

    if not results:
        raise RuntimeError("動画データを取得できませんでした")

    return results

# ==========================================
# 指標計算
# ==========================================

def safe_rate(numerator, denominator):

    if denominator == 0:
        return 0

    return round(numerator / denominator * 100, 4)


def calculate_metrics(current, previous):

    views_gain = current["views"] - previous["views"]
    likes_gain = current["likes"] - previous["likes"]
    comments_gain = current["comments"] - previous["comments"]

    return {
        **current,

        "views_gain": views_gain,
        "likes_gain": likes_gain,
        "comments_gain": comments_gain,

        "views_growth_rate": safe_rate(
            views_gain, previous["views"]
        ),

        "likes_growth_rate": safe_rate(
            likes_gain, previous["likes"]
        ),

        "comments_growth_rate": safe_rate(
            comments_gain, previous["comments"]
        ),

        "like_rate": safe_rate(
            current["likes"], current["views"]
        ),

        "comment_rate": safe_rate(
            current["comments"], current["views"]
        ),

        "engagement_rate": safe_rate(
            current["likes"] + current["comments"],
            current["views"]
        )
    }

# ==========================================
# CSV保存
# ==========================================

def save_csv(results):

    if os.path.exists(CSV_PATH):

        df = pd.read_csv(CSV_PATH)

        if not df.empty:
            df["date"] = df["date"].astype(str)

    else:
        df = pd.DataFrame(columns=COLUMNS)

    output = []

    for current in results:

        vid = current["video_id"]

        history = df[
            (df["video_id"] == vid) &
            (df["date"] < TODAY)
        ].sort_values("date")

        if history.empty:

            previous = {
                "views": 0,
                "likes": 0,
                "comments": 0
            }

            # 初回は増加率を計算しない
            row = {
                **current,
                "views_gain": 0,
                "likes_gain": 0,
                "comments_gain": 0,
                "views_growth_rate": 0,
                "likes_growth_rate": 0,
                "comments_growth_rate": 0,
                "like_rate": safe_rate(
                    current["likes"], current["views"]
                ),
                "comment_rate": safe_rate(
                    current["comments"], current["views"]
                ),
                "engagement_rate": safe_rate(
                    current["likes"] + current["comments"],
                    current["views"]
                )
            }

        else:

            prev = history.iloc[-1]

            previous = {
                "views": int(prev["views"]),
                "likes": int(prev["likes"]),
                "comments": int(prev["comments"])
            }

            row = calculate_metrics(current, previous)

        output.append(row)

    new_df = pd.DataFrame(output, columns=COLUMNS)

    # 当日分のみ置き換え、過去データは保持
    df = df[df["date"] != TODAY]

    final_df = pd.concat(
        [df, new_df],
        ignore_index=True
    )

    final_df = final_df[COLUMNS]

    final_df = final_df.sort_values(
        ["date", "video_id"]
    )

    final_df.to_csv(
        CSV_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    logger.info(f"CSV保存完了: {len(final_df)} records")

# ==========================================
# Main
# ==========================================

def main():

    logger.info("=" * 50)
    logger.info("Monitoring Start")
    logger.info(f"Date: {TODAY}")

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise ValueError("YOUTUBE_API_KEYがありません")

    videos = load_videos()

    logger.info(f"監視対象: {len(videos)} videos")

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key,
        cache_discovery=False
    )

    results = fetch_stats(youtube, videos)

    save_csv(results)

    logger.info("Monitoring Completed")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Monitoring Failed")
        sys.exit(1)
