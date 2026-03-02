import os
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}
STATE_FILE = "latest_posts.json"

BOARDS = [
    {
        "key": "INT_RECRUIT",
        "name": "국제교류본부 / Student Recruiting",
        "url": "https://cnuint.cnu.ac.kr/cnuint/notice/recruit.do",
        "webhook_env": "WEBHOOK_INT_RECRUIT",
    }
]

ID_RE = re.compile(r"(?:articleNo|no)=(\d+)", re.IGNORECASE)


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def safe_get(url: str, tries: int = 3, timeout: int = 25) -> requests.Response:
    last_err = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            print(f"[WARN] GET failed ({i+1}/{tries}) {url} -> {e}")
            time.sleep(2)
    raise last_err


def safe_post(webhook_url: str, text: str, tries: int = 3, timeout: int = 20) -> None:
    last_err = None
    for i in range(tries):
        try:
            r = requests.post(webhook_url, json={"content": text}, timeout=timeout)
            # Discord는 보통 204/200
            if r.status_code >= 400:
                raise RuntimeError(f"Discord HTTP {r.status_code}: {r.text[:200]}")
            return
        except Exception as e:
            last_err = e
            print(f"[WARN] POST failed ({i+1}/{tries}) -> {e}")
            time.sleep(2)
    raise last_err


def extract_id(s: str):
    m = ID_RE.search(s or "")
    return int(m.group(1)) if m else None


def get_recent_posts(list_url: str, limit: int = 12):
    r = safe_get(list_url)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")
    posts = []

    for row in rows[:limit]:
        a = row.select_one("a")
        if not a:
            continue

        title = a.get_text(strip=True)
        href = a.get("href", "")
        link = urljoin(list_url, href)

        post_id = extract_id(href) or extract_id(link)
        if post_id is None:
            continue

        posts.append({"id": post_id, "title": title, "link": link})

    return posts


def main():
    state = load_state()
    changed = False

    for b in BOARDS:
        webhook_url = os.environ.get(b["webhook_env"])
        if not webhook_url:
            print(f"[INFO] Missing env: {b['webhook_env']} (skip)")
            continue

        try:
            last_id = int(state.get(b["key"], 0))
            recent = get_recent_posts(b["url"], limit=12)

            new_posts = [p for p in recent if p["id"] > last_id]
            if not new_posts:
                continue

            new_posts.sort(key=lambda x: x["id"])  # 오래된 것부터

            for p in new_posts:
                msg = f"📢 [{b['name']}]\n{p['title']}\n<{p['link']}>"
                safe_post(webhook_url, msg)

            state[b["key"]] = max(p["id"] for p in new_posts)
            changed = True

        except Exception as e:
            # 여기서 죽지 말고 다음으로
            print(f"[ERROR] Board failed: {b['key']} -> {e}")

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()
