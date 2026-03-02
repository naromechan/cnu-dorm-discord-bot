import requests
from bs4 import BeautifulSoup
import json
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

BOARDS = {
    "일반공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice1",
    "입주/퇴거공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice2",
    "작업공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice3",
}

def send_discord_message(content):
    data = {"content": content}
    requests.post(WEBHOOK_URL, json=data)

def get_latest_post(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    row = soup.select_one("tbody tr")
    if not row:
        return None, None
    title_tag = row.select_one("a")
    title = title_tag.text.strip()
    link = "https://dorm.cnu.ac.kr" + title_tag["href"]
    return title, link

def load_data():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

def get_latest_posts(url, limit=5):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("tbody tr")
    
    posts = []
    for row in rows[:limit]:
        title_tag = row.select_one("a")
        if not title_tag:
            continue
        title = title_tag.text.strip()
        link = "https://dorm.cnu.ac.kr" + title_tag["href"]
        posts.append((title, link))
    
    return posts


def main():
    for name, url in BOARDS.items():
        posts = get_latest_posts(url, limit=5)
        
        for title, link in posts:
            message = f"📢 [{name}]\n{title}\n{link}"
            send_discord_message(message)
    save_data(new_data)

if __name__ == "__main__":
    main()
