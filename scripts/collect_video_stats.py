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

        with open(
            LOG_PATH,
            "r",
            encoding="utf-8"
        ) as f:
            lines = f.readlines()

        if len(lines) > 10000:

            with open(
                LOG_PATH,
                "w",
                encoding="utf-8"
            ) as f:
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
        logging.FileHandler(
            LOG_PATH,
            encoding="utf-8"
        ),
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
        raise ValueError(
            "YOUTUBE_API_KEY が設定されていません"
        )

    logger.info("YouTube API接続開始")

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    logger.info("YouTube API接続成功")

    # --------------------------------------
    # 動画ID読込
    # --------------------------------------

    try:

    with open(
    "videos.json",
    "r",
    encoding="utf-8"
    ) as f:

    config = json.load(f)

    video_configs = config["videos"]

    video_ids = [
    v["video_id"]
    for v in video_configs
    ]

    video_name_map = {
    v["video_id"\]: v["name"]
    for v

    except Exception:

        logger.exception(
            "videos.json 読込失敗"
        )
        raise

    logger.info(
        f"監視動画数: {len(video_ids)}"
    )

    # --------------------------------------
    # API取得
    # --------------------------------------

    try:

        response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        ).execute()

    except Exception:

        logger.exception(
            "YouTube API取得失敗"
        )
        raise

    rows = []

    for item in response["items"\]:

        stats = item.get(
            "statistics",
            {}
        )

        views = int(
            stats.get("viewCount", 0)
        )

        likes = int(
            stats.get("likeCount", 0)
        )

        comments = int(
            stats.get("commentCount", 0)
        )

        logger.info(
            f"{item['id']} "
            f"views={views:,} "
            f"likes={likes:,} "
            f"comments={comments:,}"
        )

        rows.append({

            "date": TODAY,

            "video_id": item["id"],

            "title":
            item["snippet"]["title"],

            "views": views,
            "likes": likes,
            "comments": comments

        })

    current_df = pd.DataFrame(rows)

    # --------------------------------------
    # 初回実行
    # --------------------------------------

    if not os.path.exists(CSV_PATH):

        logger.info(
            "初回CSV作成"
        )

        current_df["views_gain"] = 0
        current_df["likes_gain"] = 0
        current_df["comments_gain"] = 0

        current_df["views_growth_rate"] = 0.0
        current_df["likes_growth_rate"] = 0.0
        current_df["comments_growth_rate"] = 0.0

        current_df["like_rate"] = (
            current_df["likes"]
            /
            current_df["views"].replace(0, )
            * 100
        ).round(2)

        current_df["comment_rate"] = (
            current_df["comments"]
            /
            current_df["views"].replace(0, 1)
            * 100
        ).round(2)

        current_df["engagement_rate"] = (
            (
                current_df["likes"]
                + current_df["comments"]
            )
            /
            current_df["views"].replace(0, 1)
            * 100
        ).round(2)

        current_df.to_csv(
            CSV_PATH,
            index=False,
            encoding="utf-8-sig"
        )

        logger.info(
            f"初回保存件数={len(current_df)}"
        )

        return

    # --------------------------------------
    # CSV読込
    # --------------------------------------

    history_df = pd.read_csv(
        CSV_PATH
    )

    logger.info(
        f"既存CSV件数={len(history_df)}"
    )

    history_df = history_df[
        ~(
            (history_df["date"] == TODAY)
            &
            (
                history_df["video_id"].isin(
                    current_df["video_id"]
                )
            )
        )
    ]

    result_rows = []

    # --------------------------------------
    # 差分計算
    # --------------------------------------

    for _, row in current_df.iterrows():

        target = history_df[
            history_df["video_id"]
            ==
            row["video_id"]
        ]

        views = int(row["views"])
        likes = int(row["likes"])
        comments = int(row["comments"])

        if target.empty:

            views_gain = 0
            likes_gain = 0
            comments_gain = 0

            views_growth_rate = 0
            likes_growth_rate = 0
            comments_growth_rate = 0

        else:

            latest = (
                target
                .sort_values("date")
                .iloc[-1]
            )

            prev_views = int(
                latest["views"]
            )

            prev_likes = int(
                latest["likes"]
            )

            prev_comments = int(
                latest["comments"]
            )

            views_gain = (
                views - prev_views
            )

            likes_gain = (
                likes - prev_likes
            )

            comments_gain = (
                comments - prev_comments
            )

            views_growth_rate = (
                views_gain
                / prev_views
                * 100
                if prev_views > 0 else 0
            )

            likes_growth_rate = (
                likes_gain
                / prev_likes
                * 100
                if prev_likes > 0 else 0
            )

            comments_growth_rate = (
                comments_gain
                / prev_comments
                * 100
                if prev_comments > 0 else 0
            )

        logger.info(
            f"{row['video_id']} "
            f"gain={views_gain}"
        )

        result_rows.append({

            "date": TODAY,
            "video_id": row["video_id"],
            "title": row["title"],

            "views": views,
            "likes": likes,
            "comments": comments,

            "views_gain": views_gain,
            "likes_gain": likes_gain,
            "comments_gain": comments_gain,

            "views_growth_rate":
                round(
                    views_growth_rate,
                    2
                ),

            "likes_growth_rate":
                round(
                    likes_growth_rate,
                    2
                ),

            "comments_growth_rate":
                round(
                    comments_growth_rate,
                    2
                ),

            "like_rate":
                round(
                    likes / views * 100,
                    2
                )
                if views else 0,

            "comment_rate":
                round(
                    comments / views * 100,
                    2
                )
                if views else 0,

            "engagement_rate":
                round(
                    (
                        likes
                        + comments
                    )
                    / views
                    * 100,
                    2
                )
                if views else 0

        })

    result_df = pd.DataFrame(
        result_rows
    )

    final_df = pd.concat(
        [
            history_df,
            result_df
        ],
        ignore_index=True
    )

    final_df = final_df.sort_values(
        ["video_id", "date"]
    )

    final_df.to_csv(
        CSV_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    logger.info(
        f"今回追加件数={len(result_df)}"
    )

    logger.info(
        f"保存総件数={len(final_df)}"
    )

    logger.info(
        "CSV保存完了"
    )

    logger.info(
        "Monitoring End"
    )

# ==========================================
# Entry Point
# ==========================================

if __name__ == "__main__":

    try:

        main()

    except Exception:

        logger.exception(
            "処理失敗"
        )

        raise
