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
        # 模擬瀏覽器 Header，避免被封鎖
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        
        # 1. 嘗試抓取頁面
        response = requests.get(GENESYS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. 修改選擇器 (依據目前 Genesys 結構，公告通常在 .announcement-row 或 h2 a 中)
        # 我們嘗試尋找包含公告連結的標籤
        announcement_link = soup.select_one('article h2 a') or soup.select_one('.post-title a')
        
        if announcement_link:
            title = announcement_link.get_text(strip=True)
            link = announcement_link['href']
            
            # 處理相對路徑
            if link.startswith('/'):
                link = GENESYS_BASE_URL + link
            
            print(f"成功抓取: {title}")
            return title, link
        else:
            # 除錯用：如果找不到，印出部分 HTML 結構
            print("找不到公告元素，請檢查網頁結構。")
            print("HTML 內容摘要:", response.text[:500]) 
            return None, None
            
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
