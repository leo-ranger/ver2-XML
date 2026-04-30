from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os
import xml.etree.ElementTree as ET

BASE_URL = "https://fuel.tv/browse/guide/{}"
CHANNEL_ID = "fuel.tv"


# -------------------------
# SCRAPER FUNCTION
# -------------------------
def fetch_fuel_tv():
    programs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        today = datetime.utcnow().date()

        for i in range(2):  # today + tomorrow
            date = today + timedelta(days=i)
            url = BASE_URL.format(date.strftime("%Y-%m-%d"))

            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            items = page.query_selector_all("div")

            for item in items:
                text = item.inner_text().strip()

                if ":" not in text:
                    continue

                programs.append({
                    "channel": CHANNEL_ID,
                    "title": text,
                    "start": "20260101000000 +0000",  # placeholder for now
                    "stop": "20260101003000 +0000"
                })

        browser.close()

    return programs


# -------------------------
# MAIN EXECUTION (ONLY HERE)
# -------------------------
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

    ET.ElementTree(tv).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"[OK] Wrote EPG → {output_path}")
