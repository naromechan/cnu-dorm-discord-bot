import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

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

import re

def get_latest_posts(url, limit=5):
    r = requests.get(url, headers=HEADERS, timeout=10)
    print("PAGE LENGTH:", len(r.text))
    print(r.text[:1000])
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")
    posts = []

    for row in rows:
        link_tag = row.select_one("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)

        href = link_tag.get("href", "")
        print("DEBUG HREF:", href)
        # 🔥 javascript:fnView('12345') 형태 처리
        match = re.search(r"\('(\d+)'\)", href)
        if match:
            post_no = match.group(1)

            # 현재 게시판 URL에서 필요한 파라미터 추출
            base = url.split("?")[0]
            params = url.split("?")[1]

            link = f"{base}?{params}&mode=view&no={post_no}"
        else:
            # 혹시 그냥 일반 링크면
            if href.startswith("http"):
                link = href
            else:
                link = urljoin(url, href)

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
