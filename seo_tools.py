from __future__ import annotations

import email.utils
import html
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse


def build_sitemap(site_url: str, entries: list[dict]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    seen = set()
    for entry in entries:
        url = entry["url"]
        if url in seen: continue
        seen.add(url)
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(url)}</loc>")
        if entry.get("lastmod"):
            lines.append(f"    <lastmod>{html.escape(str(entry['lastmod']))}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def _rss_date(value: str) -> str:
    try:
        d = date.fromisoformat(value)
    except (ValueError, TypeError):
        d = date.today()
    dt = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
    return email.utils.format_datetime(dt)


def build_feed(site: dict, news_items: list[dict], content_items: list[dict]) -> str:
    site_url = site["url"].rstrip("/") + "/"
    items = []
    for x in news_items:
        if x.get("url", "").startswith("news/"):
            items.append({"title": x.get("title", ""), "summary": x.get("summary", ""), "date": x.get("date", ""), "url": x["url"], "category": "News"})
    for x in content_items:
        if x.get("category") == "blog" and x.get("date"):
            items.append({"title": x.get("title", ""), "summary": x.get("summary", ""), "date": x.get("date", ""), "url": x["url"], "category": "Blog"})
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    body = []
    for item in items[:30]:
        link = urljoin(site_url, item["url"])
        body.append(f'''  <item>
    <title>{html.escape(item['title'])}</title>
    <link>{html.escape(link)}</link>
    <guid isPermaLink="true">{html.escape(link)}</guid>
    <pubDate>{_rss_date(item.get('date', ''))}</pubDate>
    <category>{html.escape(item['category'])}</category>
    <description>{html.escape(item.get('summary', ''))}</description>
  </item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>noto Lab</title>
  <link>{html.escape(site_url)}</link>
  <description>{html.escape(site.get('description', ''))}</description>
  <language>ja</language>
{chr(10).join(body)}
</channel>
</rss>
'''


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("href", "src"):
            if a.get(key): self.refs.append((tag, key, a[key]))


def _resolve_local(dist: Path, page: Path, raw: str) -> Path | None:
    raw = raw.strip()
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:")): return None
    parsed = urlparse(raw)
    if parsed.scheme or parsed.netloc: return None
    path = parsed.path
    if not path: return None
    if path.startswith("/"):
        target = dist / path.lstrip("/")
    else:
        target = page.parent / path
    # normalize without requiring the target to exist
    target = Path(str(target).split("?", 1)[0])
    if target.is_dir(): target = target / "index.html"
    if target.suffix == "" and not target.exists():
        candidate = target / "index.html"
        if candidate.exists(): target = candidate
    return target


def validate_source(root: Path, content_items: list[dict], news_items: list[dict]) -> list[str]:
    errors = []
    seen_urls = set()
    for item in content_items:
        if not item.get("title"): errors.append(f"missing title: {item.get('sourcePath', item.get('url'))}")
        url = item.get("url", "")
        if url in seen_urls: errors.append(f"duplicate content URL: {url}")
        seen_urls.add(url)
        image = item.get("image", "")
        if image and not urlparse(image).scheme and image != "assets/favicon.svg" and not (root / image).exists():
            errors.append(f"missing image: {image} ({item.get('sourcePath', url)})")
    seen_news = set()
    for item in news_items:
        if not item.get("title"): errors.append(f"missing news title: {item.get('sourcePath', item.get('url'))}")
        if item.get("url") in seen_news: errors.append(f"duplicate news URL: {item.get('url')}")
        seen_news.add(item.get("url"))
    return errors


def validate_dist(dist: Path) -> list[str]:
    errors = []
    html_files = list(dist.rglob("*.html"))
    for page in html_files:
        parser = _LinkParser()
        try: parser.feed(page.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"cannot parse HTML {page.relative_to(dist)}: {exc}"); continue
        for tag, attr, raw in parser.refs:
            target = _resolve_local(dist, page, raw)
            if target is not None and not target.exists():
                errors.append(f"broken {attr}: {page.relative_to(dist)} -> {raw}")
    return errors


def fail_on_errors(errors: list[str]) -> None:
    if not errors: return
    print("\n[validation] build failed:")
    for error in errors: print(f"  - {error}")
    raise SystemExit(1)
