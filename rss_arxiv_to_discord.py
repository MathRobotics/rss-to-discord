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

MAX_EMBEDS_PER_POST = 10  # Discordの1回の投稿で許可される `embeds` の最大数
MAX_TITLE_LENGTH = 256
MAX_DESCRIPTION_LENGTH = 200
POST_DELAY = 2  # Discordへの投稿間隔（秒）

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
    title = entry.title[:MAX_TITLE_LENGTH]
    summary = entry.summary[:MAX_DESCRIPTION_LENGTH] + "..."  # 要約（長すぎる場合は200文字にカット）
    link = entry.link
    paper_id = entry.id

    # キーワードフィルタ
    if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() for keyword in KEYWORDS):
        if paper_id not in posted_papers:  # 重複防止
            new_papers.append({
                "id": paper_id,
                "title": title,
                "link": link,
                "summary": summary
            })


# Discordに埋め込みメッセージで投稿
if new_papers:
    print(f"New papers found: {len(new_papers)}")
    embeds_list = []
    for paper in new_papers:
        embeds_list.append({
            "title": paper["title"],  # タイトルをクリック可能にする
            "url": paper["link"],  # タイトルにリンクを設定
            "description": paper["summary"],  # 要約を追加
            "color": 3447003  # Discordの青系カラー（オプション）
        })

    # `embeds` を10個ごとに分割して投稿
    for i in range(0, len(embeds_list), MAX_EMBEDS_PER_POST):
        batch = embeds_list[i : i + MAX_EMBEDS_PER_POST]  # 10件ずつ取得
        payload = {
            "content": "**New arXiv Papers Matching Keywords:**",
            "embeds": batch
        }

        print("Sending payload to Discord:", json.dumps(payload, indent=4))  # デバッグ用

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            # 更新された投稿済みリストを保存
            posted_papers.extend([paper["id"] for paper in new_papers[i : i + MAX_EMBEDS_PER_POST]])
            with open(JSON_FILE, "w") as f:
                json.dump(posted_papers, f, indent=4)

        except requests.exceptions.RequestException as e:
            print(f"Error posting to Discord: {e}")
            continue  # 失敗しても他のバッチを投稿する

        time.sleep(POST_DELAY)  # 2秒遅延を挟む

else:
    print("No new papers found.")
    exit()