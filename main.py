import requests
from bs4 import BeautifulSoup
import os

# 配置
GENESYS_BASE_URL = "https://help.mypurecloud.com"
GENESYS_URL = "https://help.mypurecloud.com/announcements/"
MATTERMOST_WEBHOOK = os.getenv("MATTERMOST_WEBHOOK")
CACHE_FILE = "last_announcement.txt"

def get_latest_announcement():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(GENESYS_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取第一個公告
        article = soup.find('article')
        title_element = article.find('h2')
        title = title_element.get_text(strip=True)
        link = title_element.find('a')['href']
        
        # 處理相對路徑
        if link.startswith('/'):
            link = GENESYS_BASE_URL + link
            
        return title, link
    except Exception as e:
        print(f"抓取出錯: {e}")
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
            "text": "偵測到新公告，請相關團隊查閱。",
            "fields": [{"title": "來源", "value": "Genesys Resource Center", "short": True}]
        }]
    }
    requests.post(MATTERMOST_WEBHOOK, json=payload)

# 執行邏輯
title, link = get_latest_announcement()
if title:
    last_title = ""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            last_title = f.read().strip()

    if title != last_title:
        send_to_mattermost(title, link)
        with open(CACHE_FILE, "w") as f:
            f.write(title)