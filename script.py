import os
import json
import requests
import feedparser
import random
import time

# アカウントリストファイル
ACCOUNTS_FILE = "accounts.txt"

# RSSHubのTwitterフィードURL
RSS_BASE_URL = "https://rsshub.app/twitter/user/"

# Webhook URL（GitHub Secrets から取得）
WEBHOOK_URL = os.getenv("DISCORD_RSS_TWITTER_WEBHOOK_URL")
print("WEBHOOK_URL:", WEBHOOK_URL)

# JSONファイルのパス
ID_FILE = "read_entries.json"
wait_time = 5

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

def is_retweet_or_reply(entry):
    """エントリーがリツイート（RT）またはリプライ（Re）かどうかを判別"""
    if "title" in entry:
        title = entry.title.strip()
        if title.startswith("RT ") or title.startswith("Re "):  # "RT " または "Re " で始まる
            return True

    if "description" in entry:
        description = entry.description.strip()
        if description.startswith("RT ") or description.startswith("Re "):  # "RT " または "Re " で始まる
            return True

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

        retry_count = 0  # リトライ回数のカウント

        while retry_count < 5:  # 最大5回リトライ
            try:
                response = requests.get(rss_url, timeout=20)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))  # デフォルト10秒
                    print(f"⏳ レート制限に達しました。{retry_after}秒待機して再試行します。")
                    time.sleep(retry_after)  # 指定された時間だけ待つ
                    retry_count += 1  # リトライ回数を増やす
                    continue  # 同じURLを再試行

                if response.status_code == 200 and "rss" in response.text.lower():
                    print(f"✅ {account} のRSS取得成功: {rss_url}")
                    break  # 成功したら他のサーバーを試さない

            except requests.exceptions.RequestException as e:
                print(f"⚠️ {rss_url} のRSS取得に失敗: {e}")
                time.sleep(5)  # 失敗時も少し待機して再試行
                retry_count += 1  # リトライ回数を増やす
                continue  # 同じURLを再試行

        # すべてのサーバーで取得失敗した場合
        if response is None or response.status_code != 200:
            print(f"🚨 {account} のRSSをどのサーバーからも取得できませんでした。")
            continue

        try:
            feed = feedparser.parse(response.text)
            if not feed.entries:
                raise ValueError(f"⚠️ {account} のRSSに記事がありません。")

            for entry in reversed(feed.entries):  # 古いツイートから順に処理
                guid = entry.get("guid", entry.link)
                author = entry.get("author", "Unknown")  # 投稿者の名前
                pub_date = entry.get("pubDate", "Unknown")  # ツイートの投稿日時

                if guid not in read_ids:
                    # ✅ リツイートを除外
                    if is_retweet_or_reply(entry):
                        print(f"🔁 リツイートまたはリプライをスキップ: {entry.title}")
                        continue  # リツイートは無視
                    message = (
                        f"👤 **{author}**\n"
                        f"🕒 {pub_date}\n"
                        f"📢 **{entry.title}**\n"
                        f"🔗 {entry.link}"
                    )
                    requests.post(WEBHOOK_URL, json={"content": message})
                    new_ids.append(guid)

        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"⚠️ {account} のRSS取得中にエラー: {e}")

        time.sleep(wait_time)

    if new_ids:
        save_read_ids(read_ids + new_ids)
        print(f"✅ {len(new_ids)} 件の新しいツイートをDiscordに投稿しました。")

check_rss()
