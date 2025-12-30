#!/usr/bin/env python3
# generate_sitemap.py
# Fetch Blogger JSON feed and produce sitemap.xml
# Auto-updating GitHub Pages sitemap generator

import urllib.request
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

# BLOG FEED URL - you can increase max-results if needed
BLOG_FEED_JSON = ""

# Output file
SITEMAP_FILE = "sitemap.xml"


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SitemapGenerator/1.0)"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        return json.loads(data.decode("utf-8"))


def parse_entries(feed_json):
    entries = []
    feed = feed_json.get("feed", {})
    items = feed.get("entry", []) or []

    for e in items:
        # Extract canonical post URL
        url = None
        links = e.get("link", [])

        if isinstance(links, list):
            for link in links:
                if link.get("rel") == "alternate" and "href" in link:
                    url = link.get("href")
                    break

        if not url:
            # fallback to ID if necessary
            if isinstance(e.get("id"), dict):
                url = e["id"].get("$t")
            else:
                url = e.get("id")

        # Extract and normalize dates
        date = None
        for key in ["published", "updated"]:
            if key in e:
                raw = e[key]
                if isinstance(raw, dict) and "$t" in raw:
                    date = raw["$t"]
                else:
                    date = raw
                break

        iso_date = None
        if date:
            try:
                dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                iso_date = dt.date().isoformat()
            except Exception:
                iso_date = date[:10]  # fallback

        if url:
            entries.append({"loc": url, "lastmod": iso_date})
    return entries


def build_sitemap(entries):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    # Add homepage first
    home = ET.SubElement(urlset, "url")
    ET.SubElement(home, "loc").text = "https://zestor-pro.blogspot.com/"
    ET.SubElement(home, "changefreq").text = "daily"
    ET.SubElement(home, "priority").text = "1.0"

    for e in entries:
        tag = ET.SubElement(urlset, "url")
        ET.SubElement(tag, "loc").text = e["loc"]
        if e.get("lastmod"):
            ET.SubElement(tag, "lastmod").text = e["lastmod"]

    rough = ET.tostring(urlset, "utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")
    return pretty


def read_existing(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_if_changed(path, content_bytes):
    old = read_existing(path)
    if old == content_bytes:
        print("No changes in sitemap.xml")
        return False
    with open(path, "wb") as f:
        f.write(content_bytes)
    print("Updated sitemap.xml")
    return True


def main():
    print("Fetching Blogger feed:", BLOG_FEED_JSON)
    feed_json = fetch_json(BLOG_FEED_JSON)

    print("Parsing entries...")
    entries = parse_entries(feed_json)

    print(f"Found {len(entries)} posts")

    content = build_sitemap(entries)
    changed = write_if_changed(SITEMAP_FILE, content)

    if not changed:
        print("Nothing to commit.")
    return 0


if __name__ == "__main__":
    exit(main())
