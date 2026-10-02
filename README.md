# Studio Cabana Monitoring

YouTube Data API と GitHub Actions を利用して、STUDIO CABANA の監視対象動画の統計情報を日次収集するリポジトリです。

## 概要

毎日自動で以下の指標を取得し、CSVへ蓄積します。

- 再生数 (Views)
- 高評価数 (Likes)
- コメント数 (Comments)

さらに前日との差分および増加率も計算します。

### 自動計算項目

- views_gain
- likes_gain
- comments_gain

- views_growth_rate
- likes_growth_rate
- comments_growth_rate

- like_rate
- comment_rate
- engagement_rate

---

## ディレクトリ構成

```text
studio-cabana-monitoring/
│
├─ .github/
│   └─ workflows/
│       └─ youtube_video_stats.yml
│
├─ scripts/
│   └─ collect_video_stats.py
│
├─ data/
│   └─ video_daily_stats.csv
│
├─ videos.json
├─ requirements.txt
└─ README.md
