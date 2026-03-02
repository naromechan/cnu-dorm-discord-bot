import requests
from bs4 import BeautifulSoup
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BOARDS = {
    "일반공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice1",
    "입주/퇴거공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice2",
    "작업공지": "https://dorm.cnu.ac.kr/html/kr/board/board.php?bo_table=notice3",
}

def send_discord_message(content):
    try:
        requests.post(WEBHOOK_URL, json={"content": content})
    except:
        pass

def get_latest_posts(url, limit=5):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.select("tr")
        posts = []

        for row in rows:
            link_tag = row.find("a")
            if link_tag and "board.php" in link_tag.get("href", ""):
                title = link_tag.text.strip()
                link = "https://dorm.cnu.ac.kr" + link_tag["href"]
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

        for title, link in posts:
            message = f"📢 [{name}]\n{title}\n{link}"
            send_discord_message(message)

if __name__ == "__main__":
    main()
