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


def get_latest_post(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "html.parser")
    row = soup.select_one("table tbody tr")

    if not row:
        return None, None, None

    link_tag = row.select_one("a")
    if not link_tag:
        return None, None, None

    title = link_tag.get_text(strip=True)
    href = link_tag.get("href", "")

    link = urljoin(url, href)

    match = re.search(r"no=(\d+)", href)
    post_no = match.group(1) if match else None

    return title, link, post_no


def main():
    old_data = load_data()
    new_data = old_data.copy()

    for name, url in BOARDS.items():
        title, link, post_no = get_latest_post(url)

        if not post_no:
            continue

        if old_data.get(name) != post_no:
            message = f"📢 [{name}]\n{title}\n{link}"
            send_discord_message(message)
            new_data[name] = post_no

    save_data(new_data)


if __name__ == "__main__":
    main()
