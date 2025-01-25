import os
import json
import requests
import feedparser

# RSSフィードURL（監視するTwitterアカウント）
RSS_URL = "https://rsshub.app/twitter/user/bostondynamics"
# Webhook URL（GitHub Secrets から取得）
WEBHOOK_URL = os.getenv("DISCORD_RSS_TWITTER_WEBHOOK_URL")
print("WEBHOOK_URL:", WEBHOOK_URL)

# JSONファイルのパス
ID_FILE = "read_entries.json"

def load_read_ids():
    """JSONファイルから既読のIDリストを読み込む"""
    try:
        with open(ID_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_read_ids(ids):
    """新しいIDリストをJSONファイルに保存"""
    with open(ID_FILE, "w") as file:
        json.dump(ids, file, indent=2)

def check_rss():
    """RSSを取得し、新しい記事があればDiscordに投稿"""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.text)
    read_ids = load_read_ids()
    new_ids = []

    for entry in feed.entries:
        guid = entry.get("guid", entry.link)  # `guid`がなければ`link`を代用
        if guid not in read_ids:
            message = f"📢 **{entry.title}**\n{entry.link}"
            requests.post(WEBHOOK_URL, json={"content": message})
            new_ids.append(guid)

    if new_ids:
        save_read_ids(read_ids + new_ids)  # JSONファイルを更新

check_rss()
