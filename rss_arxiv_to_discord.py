import feedparser
import json
import requests
import os

# 設定
ARXIV_RSS_URL = "https://arxiv.org/rss/cs.RO"  # 監視するカテゴリ
KEYWORDS = ["humanoid", "robot", "biped"]  # 検索キーワード
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_RSS_ARXIV_WEBHOOK_URL")  # GitHub Secretsから取得
JSON_FILE = "posted_arxiv_papers.json"

MAX_TITLE_LENGTH = 256
MAX_DESCRIPTION_LENGTH = 4000

# 既存データの読み込み
try:
    with open(JSON_FILE, "r") as f:
        posted_papers = json.load(f)
except FileNotFoundError:
    posted_papers = []

# RSSフィードを取得
feed = feedparser.parse(ARXIV_RSS_URL)
new_papers = []

for entry in feed.entries:
    title = entry.title
    summary = entry.summary[:200] + "..."  # 要約（長すぎる場合は200文字にカット）
    link = entry.link
    paper_id = entry.id

    # キーワードフィルタ
    if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() for keyword in KEYWORDS):
        if paper_id not in posted_papers:  # 重複防止
            new_papers.append({
                "title": title,
                "link": link,
                "summary": summary
            })
            posted_papers.append(paper_id)


# Discordに埋め込みメッセージで投稿
embeds = []
for paper in new_papers:
    embeds.append({
        "title": paper["title"],  # タイトルをクリック可能にする
        "url": paper["link"],  # タイトルにリンクを設定
        "description": paper["summary"],  # 要約を追加
        "color": 3447003  # Discordの青系カラー（オプション）
    })

for embed in embeds:
    embed["title"] = embed["title"][:MAX_TITLE_LENGTH]  # 256文字制限
    # embed["description"] = embed["description"][:MAX_DESCRIPTION_LENGTH]  # 4000文字制限

payload = {
    "content": "**New arXiv Papers Matching Keywords:**",
    "embeds": embeds
}

if not embeds:
    print("No new papers found.")
    exit()
try:
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()
    # 更新された投稿済みリストを保存
    with open(JSON_FILE, "w") as f:
        json.dump(posted_papers, f, indent=4)

except requests.exceptions.RequestException as e:
    print(f"Error posting to Discord: {e}")