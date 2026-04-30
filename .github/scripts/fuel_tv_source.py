if __name__ == "__main__":
    import os
    import xml.etree.ElementTree as ET

    programs = fetch_fuel_tv()

    # ✅ force path relative to repo root
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    output_path = os.path.join(
        BASE_DIR,
        "download_EPG/individual/Sports/fueltv.xml"
    )

    # ensure folders exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # build VERY basic XML (just to test pipeline)
    tv = ET.Element("tv")

    for p in programs:
        prog = ET.SubElement(tv, "programme")
        prog.set("channel", p["channel"])
        prog.set("start", p["start"])
        prog.set("stop", p["stop"])

        title = ET.SubElement(prog, "title")
        title.text = p["title"]

    tree = ET.ElementTree(tv)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print(f"[FuelTV] Wrote: {output_path}")
