import feedparser
import json
import requests
import os
import time

# 設定
ARXIV_RSS_URL = "https://arxiv.org/rss/cs.RO"  # 監視するカテゴリ
KEYWORDS = ["humanoid", "robot", "biped"]  # 検索キーワード
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_RSS_ARXIV_WEBHOOK_URL")  # GitHub Secretsから取得
JSON_FILE = "posted_arxiv_papers.json"

print("WEBHOOK_URL:", DISCORD_WEBHOOK_URL)

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
    summary = entry.summary
    link = entry.link
    paper_id = entry.id

    # キーワードフィルタ
    if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() for keyword in KEYWORDS):
        if paper_id not in posted_papers:  # 重複防止
            new_papers.append({
                "title": title,
                "link": link
            })
            posted_papers.append(paper_id)

# Discordに1件ずつ投稿
for paper in new_papers:
    message = f"**New arXiv Paper:**\n📄 **{paper['title']}**\n🔗 {paper['link']}"
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        response.raise_for_status()
        print(f"Posted: {paper['title']}")

        time.sleep(1)  # 連続リクエストを避けるために1秒待機

    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord: {e}")

# 更新された投稿済みリストを保存
with open(JSON_FILE, "w") as f:
    json.dump(posted_papers, f, indent=4)