import os
import json
import requests
import feedparser

# アカウントリストファイル
ACCOUNTS_FILE = "accounts.txt"

# RSSHubのTwitterフィードURL
RSS_BASE_URL = "https://rsshub.app/twitter/user/"

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

def load_accounts():
    """accounts.txt から監視するTwitterアカウントを読み込む"""
    try:
        with open(ACCOUNTS_FILE, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"⚠️ {ACCOUNTS_FILE} が見つかりません！")
        return []

def check_rss():
    """複数のTwitterアカウントのRSSを取得し、新しい記事があればDiscordに投稿"""
    read_ids = load_read_ids()
    new_ids = []

    accounts = load_accounts()
    if not accounts:
        print("⚠️ 監視するTwitterアカウントがありません。")
        return

    for account in accounts:
        rss_url = f"{RSS_BASE_URL}{account}"
        print(f"🔍 {account} のRSSを取得中: {rss_url}")

        try:
            response = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ {account} のRSS取得に失敗 (HTTP {response.status_code})")
                continue

            feed = feedparser.parse(response.text)
            if not feed.entries:
                print(f"⚠️ {account} のRSSに記事がありません。")
                continue

            for entry in reversed(feed.entries):
                guid = entry.get("guid", entry.link)
                if guid not in read_ids:
                    message = f"📢 **{entry.title}**\n{entry.link}"
                    requests.post(WEBHOOK_URL, json={"content": message})
                    new_ids.append(guid)

        except requests.exceptions.RequestException as e:
            print(f"⚠️ {account} のRSS取得中にエラー: {e}")

    if new_ids:
        save_read_ids(read_ids + new_ids)
        print(f"✅ {len(new_ids)} 件の新しいツイートをDiscordに投稿しました。")

check_rss()
