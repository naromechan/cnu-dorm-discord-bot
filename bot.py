import requests
from bs4 import BeautifulSoup
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BOARDS = {
    "입주/퇴거공지": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub05_0501&site_dvs_cd=kr&menu_dvs_cd=030601",
    "일반공지": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub03_0301&site_dvs_cd=kr&menu_dvs_cd=0302",
    "작업공지": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub03_0302&site_dvs_cd=kr&menu_dvs_cd=0303",
}

BASE_URL = "https://dorm.cnu.ac.kr"

def send_discord_message(content):
    requests.post(WEBHOOK_URL, json={"content": content})

def get_latest_posts(url, limit=5):
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "utf-8"   # ✅ 한글 깨짐 방지

    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")
    posts = []

    for row in rows:
        link_tag = row.select_one("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)

        href = link_tag.get("href")
        if not href:
            continue

        # ✅ 게시글 상세페이지 링크 정확히 생성
        if href.startswith("http"):
            link = href
        else:
            link = BASE_URL + href

        posts.append((title, link))

        if len(posts) >= limit:
            break

    return posts

def main():
    for name, url in BOARDS.items():
        posts = get_latest_posts(url, limit=5)

        for title, link in posts:
            message = f"📢 [{name}]\n{title}\n{link}"
            send_discord_message(message)

if __name__ == "__main__":
    main()
