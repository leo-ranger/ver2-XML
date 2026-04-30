from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re

BASE_URL = "https://fuel.tv/browse/guide/{}"
CHANNEL_ID = "fuel.tv"


def parse_block(text):
    """
    Attempts to extract:
    time, title, description
    """

    # Example:
    # 12:35 AM
    # Bubba's World - Season 2 - The Shift
    # Motorsports
    # description...
    # 30 mins

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    time_match = re.match(r"(\d{1,2}:\d{2}\s?[APMapm]{2})", lines[0]) if lines else None
    if not time_match:
        return None

    time_str = time_match.group(1)

    title = lines[1] if len(lines) > 1 else "Unknown"
    desc = lines[3] if len(lines) > 3 else ""

    return time_str, title, desc


def fetch_fuel_tv():
    programs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        today = datetime.utcnow().date()

        for i in range(2):  # today + tomorrow
            date = today + timedelta(days=i)
            url = BASE_URL.format(date.strftime("%Y-%m-%d"))

            print(f"[EPG] {url}")

            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)

            # ⚠️ You will refine this selector later
            cards = page.query_selector_all("div")

            day_programs = []

            for card in cards:
                text = card.inner_text()

                # IMAGE extraction (important part)
                img_el = card.query_selector("img")
                img = img_el.get_attribute("src") if img_el else None

                parsed = parse_block(text)
                if not parsed:
                    continue

                time_str, title, desc = parsed

                dt = datetime.strptime(
                    f"{date} {time_str.upper()}",
                    "%Y-%m-%d %I:%M %p"
                )

                day_programs.append({
                    "channel": CHANNEL_ID,
                    "title": title,
                    "desc": desc,
                    "icon": img,
                    "start": dt,
                })

            # sort timeline
            day_programs.sort(key=lambda x: x["start"])

            # build stop times
            for i, p in enumerate(day_programs):
                if i + 1 < len(day_programs):
                    stop = day_programs[i + 1]["start"]
                else:
                    stop = p["start"] + timedelta(minutes=30)

                programs.append({
                    "channel": p["channel"],
                    "title": p["title"],
                    "desc": p["desc"],
                    "icon": p["icon"],
                    "start": p["start"].strftime("%Y%m%d%H%M%S +0000"),
                    "stop": stop.strftime("%Y%m%d%H%M%S +0000"),
                })

        browser.close()

    return programs
