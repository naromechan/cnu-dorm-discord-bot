import requests
from bs4 import BeautifulSoup
import os
import json
import re
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

DATA_FILE = "latest_posts.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_discord_message(content):
    requests.post(WEBHOOK_URL, json={"content": content})


def get_recent_posts(url, limit=10):
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("table tbody tr")

    posts = []

    for row in rows[:limit]:
        link_tag = row.select_one("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        link = urljoin(url, href)

        match = re.search(r"no=(\d+)", href)
        if not match:
            continue

        post_no = int(match.group(1))

        posts.append({
            "title": title,
            "link": link,
            "no": post_no
        })

    return posts


def main():
    old_data = load_data()
    new_data = old_data.copy()

    for name, url in BOARDS.items():
        recent_posts = get_recent_posts(url)

        last_saved_no = int(old_data.get(name, 0))

        # 저장된 번호보다 큰 것만 필터
        new_posts = [p for p in recent_posts if p["no"] > last_saved_no]

        if not new_posts:
            continue

        # 오래된 것부터 보내기 위해 오름차순 정렬
        new_posts.sort(key=lambda x: x["no"])

        for post in new_posts:
            message = f"📢 [{name}]\n{post['title']}\n{post['link']}"
            send_discord_message(message)

        # 가장 최신 번호 저장
        new_data[name] = max(p["no"] for p in new_posts)

    save_data(new_data)


if __name__ == "__main__":
    main()
