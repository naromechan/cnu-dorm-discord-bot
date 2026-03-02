import os
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

# ✅ 연결 재사용(속도/안정성↑)
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

STATE_FILE = "latest_posts.json"

BOARDS = [
    {
        "key": "INT_RECRUIT",
        "name": "국제교류본부 / Student Recruiting",
        "url": "https://cnuint.cnu.ac.kr/cnuint/notice/recruit.do",
        "webhook_env": "WEBHOOK_INT_RECRUIT",
    },
    {
        "key": "INT_EVENT",
        "name": "국제교류본부 / Event",
        "url": "https://cnuint.cnu.ac.kr/cnuint/notice/event.do",
        "webhook_env": "WEBHOOK_INT_EVENT",
    },
    {
        "key": "INT_JOB",
        "name": "국제교류본부 / Job & Career",
        "url": "https://cnuint.cnu.ac.kr/cnuint/notice/job.do",
        "webhook_env": "WEBHOOK_INT_JOB",
    },
    {
        "key": "HUM_NOTICE",
        "name": "인문대 / 공지",
        "url": "https://human.cnu.ac.kr/human/community/notice.do",
        "webhook_env": "WEBHOOK_HUM_NOTICE",
    },
    {
        "key": "JPN_NOTICE",
        "name": "일어일문과 / Main Notice(학부)",
        "url": "https://cnujapan.cnu.ac.kr/japanese/notice/undergraduate.do",
        "webhook_env": "WEBHOOK_JPN_NOTICE",
    },
    {
        "key": "PLUS_NEWS",
        "name": "학교공지 / 새소식",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0701&site_dvs_cd=kr&menu_dvs_cd=0701",
        "webhook_env": "WEBHOOK_PLUS_NEWS",
    },
    {
        "key": "PLUS_ACAD",
        "name": "학교공지 / 학사정보",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0702&site_dvs_cd=kr&menu_dvs_cd=0702",
        "webhook_env": "WEBHOOK_PLUS_ACAD",
    },
    {
        "key": "PLUS_EDU",
        "name": "학교공지 / 교육정보",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0704&site_dvs_cd=kr&menu_dvs_cd=0704",
        "webhook_env": "WEBHOOK_PLUS_EDU",
    },
    {
        "key": "PLUS_STARTUP",
        "name": "학교공지 / 사업단 창업&교육",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0709&site_dvs_cd=kr&menu_dvs_cd=0709",
        "webhook_env": "WEBHOOK_PLUS_STARTUP",
    },
    {
        "key": "PLUS_HIRE",
        "name": "학교공지 / 채용&초빙",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0705&site_dvs_cd=kr&menu_dvs_cd=0705",
        "webhook_env": "WEBHOOK_PLUS_HIRE",
    },
    {
        "key": "PLUS_SEMINAR",
        "name": "학교공지 / 세미나&행사",
        "url": "https://plus.cnu.ac.kr/_prog/_board/?code=sub010714&site_dvs_cd=kr&menu_dvs_cd=0712",
        "webhook_env": "WEBHOOK_PLUS_SEMINAR",
    },
    {
    "key": "DORM_MOVE",
    "name": "기숙사 / 입주·퇴거 공지",
    "url": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub05_0501&site_dvs_cd=kr&menu_dvs_cd=030601",
    "webhook_env": "WEBHOOK_DORM_MOVE",
    },
    {
    "key": "DORM_GENERAL",
    "name": "기숙사 / 일반 공지",
    "url": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub03_0301&site_dvs_cd=kr&menu_dvs_cd=0302",
    "webhook_env": "WEBHOOK_DORM_GENERAL",
    },
    {
    "key": "DORM_WORK",
    "name": "기숙사 / 작업 공지",
    "url": "https://dorm.cnu.ac.kr/_prog/_board/?code=sub03_0302&site_dvs_cd=kr&menu_dvs_cd=0303",
    "webhook_env": "WEBHOOK_DORM_WORK",
    },
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


# ✅ 속도/안정 밸런스 추천값
def safe_get(url: str, tries: int = 4, timeout: int = 35) -> requests.Response:
    last_err = None
    for i in range(tries):
        try:
            r = SESSION.get(url, timeout=timeout)
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
        start = time.time()
        print(f"[START] {b['key']} {b['url']}")

        webhook_url = os.environ.get(b["webhook_env"])
        if not webhook_url:
            print(f"[INFO] Missing env: {b['webhook_env']} (skip)")
            continue

        try:
            last_id = int(state.get(b["key"], 0))
            recent = get_recent_posts(b["url"], limit=12)

            new_posts = [p for p in recent if p["id"] > last_id]
            if not new_posts:
                print(f"[DONE]  {b['key']} no new posts ({time.time()-start:.1f}s)")
                time.sleep(1)
                continue

            new_posts.sort(key=lambda x: x["id"])

            for p in new_posts:
                msg = f"📢 [{b['name']}]\n{p['title']}\n<{p['link']}>"
                safe_post(webhook_url, msg)

            state[b["key"]] = max(p["id"] for p in new_posts)
            changed = True

        except Exception as e:
            print(f"[ERROR] Board failed: {b['key']} -> {e}")

        print(f"[DONE]  {b['key']} took {time.time()-start:.1f}s")
        time.sleep(1)  # ✅ 보드 간 쉬기

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()
