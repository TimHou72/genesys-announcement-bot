import requests
import feedparser
import os

# 配置
# Genesys Cloud Announcements RSS Feed
RSS_URL = "https://help.mypurecloud.com/announcements/feed/"
MATTERMOST_WEBHOOK = os.getenv("MATTERMOST_WEBHOOK")
CACHE_FILE = "last_announcement.txt"

def get_latest_from_rss():
    try:
        # 下載並解析 RSS
        feed = feedparser.parse(RSS_URL)
        
        if not feed.entries:
            print("RSS 內容為空")
            return None, None
            
        # 取得第一條公告
        first_entry = feed.entries[0]
        title = first_entry.title
        link = first_entry.link
        
        return title, link
    except Exception as e:
        print(f"RSS 解析失敗: {e}")
        return None, None

def get_style(title):
    t = title.lower()
    if any(word in t for word in ["deprecation", "removal", "notice"]):
        return "#FF3333", "🔴 棄用通知"
    if any(word in t for word in ["new", "feature", "launch"]):
        return "#2ECC71", "🟢 新功能"
    if "api" in t:
        return "#3498DB", "🔵 API 更新"
    return "#888888", "⚪ 一般公告"

def send_to_mattermost(title, link):
    color, tag = get_style(title)
    payload = {
        "username": "Genesys Cloud Bot",
        "attachments": [{
            "color": color,
            "title": f"[{tag}] {title}",
            "title_link": link,
            "text": "偵測到 Genesys Cloud 發布了新公告。",
            "fields": [{"title": "來源", "value": "Genesys Resource Center (RSS)", "short": True}]
        }]
    }
    requests.post(MATTERMOST_WEBHOOK, json=payload)

# 執行邏輯
title, link = get_latest_from_rss()

if title:
    last_title = ""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            last_title = f.read().strip()

    if title != last_title:
        print(f"發現新公告: {title}")
        send_to_mattermost(title, link)
        with open(CACHE_FILE, "w") as f:
            f.write(title)
    else:
        print(f"公告已存在，跳過。")
else:
    print("未能抓取到任何資料。")
