# Studio Cabana Monitoring

STUDIO CABANAの特定動画を日次監視し、YouTube Data API v3 と GitHub Actions を利用して統計データをCSVへ蓄積するプロジェクトです。

## 取得データ

毎日以下を取得します。

- 再生数 (views)
- 高評価数 (likes)
- コメント数 (comments)

あわせて以下を自動計算します。

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

# システム構成

```text
GitHub Actions
        ↓
YouTube Data API
        ↓
collect_video_stats.py
        ↓
video_daily_stats.csv
        ↓
Git Commit & Push
```

---

# ディレクトリ構成

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
```

---

# セットアップ

## 1. リポジトリ作成

```bash
git clone https://github.com/<YOUR_ACCOUNT>/studio-cabana-monitoring.git

cd studio-cabana-monitoring
```

---

## 2. YouTube Data API v3 を有効化

Google Cloud Console

```text
https://console.cloud.google.com
```

でプロジェクト作成後

```text
YouTube Data API v3
```

を有効化。

---

## 3. APIキーを作成

```text
APIs & Services
↓
Credentials
↓
Create Credentials
↓
API Key
```

---

## 4. GitHub Secret 登録

GitHub

```text
Settings
↓
Secrets and variables
↓
Actions
↓
New repository secret
```

登録

```text
Name:
YOUTUBE_API_KEY

Value:
取得したAPIキー
```

---

## 5. GitHub Actions権限設定

GitHub

```text
Settings
↓
Actions
↓
General
↓
Workflow permissions
```

を開く。

選択

```text
Read and write permissions
```

推奨

```text
Allow GitHub Actions to create and approve pull requests
```

も有効化。

---

## 6. requirements.txt

```text
pandas
google-api-python-client
```

---

## 7. 監視対象動画設定

videos.json

```json
{
  "videos": [
    "VIDEO_ID_1",
    "VIDEO_ID_2",
    "VIDEO_ID_3",
    "VIDEO_ID_4",
    "VIDEO_ID_5"
  ]
}
```

例

```text
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

↓

```text
dQw4w9WgXcQ
```

を登録。

---

## 8. Pythonスクリプト配置

```text
scripts/collect_video_stats.py
```

に監視スクリプトを配置。

---

## 9. Workflow配置

```text
.github/workflows/youtube_video_stats.yml
```

workflowには以下を含める。

```yaml
permissions:
  contents: write
```

---

## 10. 初回Push

```bash
git add .

git commit -m "initial setup"

git push
```

---

# 動作確認

GitHub

```text
Actions
↓
YouTube Video Daily Stats
↓
Run workflow
```

を実行。

成功すると

```text
data/video_
