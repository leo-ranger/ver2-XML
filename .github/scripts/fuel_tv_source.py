from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import re
import os
import xml.etree.ElementTree as ET

BASE_URL = "https://fuel.tv/browse/guide/{}"
CHANNEL_ID = "fuel.tv"


# -----------------------------
# ROBUST BLOCK PARSER
# -----------------------------
def parse_block(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return None

    # Find time anywhere in block
    time_str = None
    for l in lines:
        match = re.match(r"(\d{1,2}:\d{2}\s?[APMapm]{2})", l)
        if match:
            time_str = match.group(1)
            break

    if not time_str:
        return None

    # Remove time line(s)
    cleaned = [l for l in lines if time_str not in l]

    title = cleaned[0] if len(cleaned) > 0 else "Unknown"
    desc = max(cleaned[1:], key=len) if len(cleaned) > 1 else ""

    return time_str, title, desc


# -----------------------------
# MAIN SCRAPER
# -----------------------------
def fetch_fuel_tv():
    programs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        today = datetime.utcnow().date()

        for i in range(2):  # today + tomorrow
            date = today + timedelta(days=i)
            url = BASE_URL.format(date.strftime("%Y-%m-%d"))

            print(f"[FuelTV] Fetching {url}")

            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)

            # ⚠️ still broad selector (we refine later)
            cards = page.query_selector_all("div")

            # ✅ FIXED: must be OUTSIDE loop (was causing indentation crash)
            day_programs = []

            for card in cards:
                text = card.inner_text().strip()

                # -------------------------
                # IMAGE EXTRACTION (safe)
                # -------------------------
                img_el = card.query_selector("img")
                img = None
                if img_el:
                    img = img_el.get_attribute("src") or img_el.get_attribute("data-src")

                parsed = parse_block(text)
                if not parsed:
                    continue

                time_str, title, desc = parsed

                try:
                    dt = datetime.strptime(
                        f"{date} {time_str.upper()}",
                        "%Y-%m-%d %I:%M %p"
                    )
                except:
                    continue

                day_programs.append({
                    "channel": CHANNEL_ID,
                    "title": title,
                    "desc": desc,
                    "icon": img,
                    "start": dt,
                })

            # -----------------------------
            # SORT TIMELINE
            # -----------------------------
            day_programs.sort(key=lambda x: x["start"])

            # -----------------------------
            # BUILD STOP TIMES
            # -----------------------------
            for i, p_item in enumerate(day_programs):

                if i + 1 < len(day_programs):
                    stop_dt = day_programs[i + 1]["start"]
                else:
                    stop_dt = p_item["start"] + timedelta(minutes=30)

                programs.append({
                    "channel": p_item["channel"],
                    "title": p_item["title"],
                    "desc": p_item["desc"],
                    "icon": p_item["icon"],
                    "start": p_item["start"].strftime("%Y%m%d%H%M%S +0000"),
                    "stop": stop_dt.strftime("%Y%m%d%H%M%S +0000"),
                })

        browser.close()

    return programs


# -----------------------------
# OPTIONAL LOCAL TEST RUN
# -----------------------------
if __name__ == "__main__":

    programs = fetch_fuel_tv()

    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../")
    )

    output_path = os.path.join(
        BASE_DIR,
        "download_EPG/individual/Sports/fueltv.xml"
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    tv = ET.Element("tv")

    for p in programs:
        prog = ET.SubElement(tv, "programme")
        prog.set("channel", p["channel"])
        prog.set("start", p["start"])
        prog.set("stop", p["stop"])

        title = ET.SubElement(prog, "title")
        title.text = p["title"]

        if p.get("desc"):
            desc = ET.SubElement(prog, "desc")
            desc.text = p["desc"]

        if p.get("icon"):
            icon = ET.SubElement(prog, "icon")
            icon.set("src", p["icon"])

    ET.ElementTree(tv).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"[OK] Wrote EPG → {output_path}")
