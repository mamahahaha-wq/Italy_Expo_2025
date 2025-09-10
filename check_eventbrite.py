import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

# --- 設定 ---
PAGE_URL = "https://www.eventbrite.com/o/italy-expo-2025-osaka-107252340551"
SEEN_FILE = "seen.json"
RSS_FILE = "feed.xml"
SITE_NAME = "Italy Expo 2025 Osaka - Eventbrite"
DESCRIPTION = "Auto-generated RSS for new Eventbrite events (Italy Expo 2025 Osaka)"
# ----------------------------------------------------------------

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RSS-Checker/1.0; +https://github.com/yourname)"
}

def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def extract_event_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/e/" in href:
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            normalized = parsed.scheme + "://" + parsed.netloc + parsed.path
            title = (a.get_text() or "").strip() or normalized
            links[normalized] = title
    return links

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 初回実行時は空のリストを返す
        return []

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

def escape_xml(s):
    return (s.replace("&","&amp;").replace("<","&lt;")
              .replace(">","&gt;").replace('"',"&quot;").replace("'", "&apos;"))

def make_rss(items):
    now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss_items = []
    for it in items:
        rss_items.append(f"""
  <item>
    <title>{escape_xml(it['title'])}</title>
    <link>{escape_xml(it['link'])}</link>
    <guid isPermaLink="true">{escape_xml(it['link'])}</guid>
    <pubDate>{it['pubDate']}</pubDate>
    <description>{escape_xml(it.get('description',''))}</description>
  </item>""")
    rss = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
<channel>
  <title>{escape_xml(SITE_NAME)}</title>
  <link>{escape_xml(PAGE_URL)}</link>
  <description>{escape_xml(DESCRIPTION)}</description>
  <lastBuildDate>{now}</lastBuildDate>
{''.join(rss_items)}
</channel>
</rss>"""
    with open(RSS_FILE, "w", encoding="utf-8") as f:
        f.write(rss)

def main():
    html = fetch_page(PAGE_URL)
    links = extract_event_links(html, PAGE_URL)

    seen = load_seen()
    seen_set = set(seen)

    # 新規リンクをリスト化
    new_links = []
    for link, title in links.items():
        if link not in seen_set:
            new_links.append({"link": link, "title": title, "pubDate": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")})
            seen_set.add(link)

    # 全てのリンクから RSS 作成（最新順）
    all_items = []
    for link in reversed(list(seen_set)):
        t = links.get(link, link)
        all_items.append({"link": link, "title": t, "pubDate": datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")})

    make_rss(all_items)
    save_seen(list(seen_set))

    print(f"Processed {len(links)} total links, {len(new_links)} new.")
    if new_links:
        print(f"RSS updated: {RSS_FILE}")
    else:
        print("No new links, but RSS file regenerated.")

if __name__ == "__main__":
    main()
