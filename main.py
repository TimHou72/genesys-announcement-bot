import requests
import feedparser
import os
import hashlib
from datetime import datetime

# 配置
RSS_URL = "https://help.mypurecloud.com/announcements/feed/"
MATTERMOST_WEBHOOK = os.getenv("MATTERMOST_WEBHOOK")
CACHE_FILE = "sent_hashes.txt"
MAX_CACHE_SIZE = 50  # 只保留最近 50 筆紀錄

def get_hash(text):
    """將標題轉為雜湊值，比對更準確"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_sent_hashes():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    return []

def save_hashes(hashes):
    # 只保留最後 50 筆，避免檔案過大
    with open(CACHE_FILE, "w") as f:
        f.write("\n".join(hashes[-MAX_CACHE_SIZE:]))

def get_style(title):
    t = title.lower()
    if any(x in t for x in ["deprecation", "removal", "notice", "end of"]):
        return "#FF3333", "🔴 棄用/重大通知"
    if any(x in t for x in ["new", "feature", "launch", "introduced"]):
        return "#2ECC71", "🟢 新功能上線"
    if "api" in t:
        return "#3498DB", "🔵 API 變更"
    return "#888888", "⚪ 一般公告"

def send_to_mattermost(entry):
    color, tag = get_style(entry.title)
    
    # 格式化時間 (RSS 的時間通常是 GMT)
    published = entry.get('published', '未知時間')
    
    # 擷取摘要 (取前 100 字)
    summary = BeautifulSoup(entry.summary, "html.parser").get_text()[:100] + "..."

    payload = {
        "username": "Genesys Cloud Bot",
        "attachments": [{
            "color": color,
            "title": f"[{tag}] {entry.title}",
            "title_link": entry.link,
            "text": f"**發布時間**: {published}\n**內容摘要**: {summary}",
            "fields": [
                {"title": "來源", "value": "Genesys Resource Center", "short": True},
                {"title": "類別", "value": tag, "short": True}
            ],
            "footer": "Genesys Cloud 自動化監控",
            "ts": int(datetime.now().timestamp())
        }]
    }
    try:
        r = requests.post(MATTERMOST_WEBHOOK, json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"發送失敗: {e}")

# 執行邏輯
if __name__ == "__main__":
    from bs4 import BeautifulSoup # 用於處理摘要中的 HTML

    sent_hashes = get_sent_hashes()
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("無法取得 RSS Feed 或內容為空")
        exit()

    new_hashes = []
    has_update = False

    # 倒序處理（從舊到新發送）
    for entry in reversed(feed.entries[:10]):
        h = get_hash(entry.title)
        if h not in sent_hashes:
            print(f"處理新公告: {entry.title}")
            send_to_mattermost(entry)
            sent_hashes.append(h)
            has_update = True

    if has_update:
        save_hashes(sent_hashes)
    else:
        print("檢查完成，無新公告。")
