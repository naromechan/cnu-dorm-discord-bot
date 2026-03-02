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
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except:
        pass

def get_latest_posts(url, limit=5):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.select("table tbody tr")
        posts = []

        for row in rows:
            link_tag = row.select_one("a")
            if not link_tag:
                continue

            title = link_tag.text.strip()
            href = link_tag.get("href")

            if not href:
                continue

            if not href.startswith("http"):
                link = BASE_URL + href
            else:
                link = href

            posts.append((title, link))

            if len(posts) >= limit:
                break

        return posts

    except Exception as e:
        send_discord_message(f"❌ 에러 발생: {e}")
        return []

def main():
    for name, url in BOARDS.items():
        posts = get_latest_posts(url, limit=5)

        if not posts:
            send_discord_message(f"⚠ [{name}] 게시글을 찾지 못했습니다.")
            continue

        for title, link in posts:
            message = f"📢 [{name}]\n{title}\n{link}"
            send_discord_message(message)

if __name__ == "__main__":
    main()
