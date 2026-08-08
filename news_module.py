from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from markdown_utils import markdown_to_html_with_toc
from site_common import esc, favicon_links, header, local_url, og_meta


def _front_value(value: str):
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}: return True
    if low in {"false", "no", "off"}: return False
    return value


def _one_month_ago(today: date) -> date:
    year, month = today.year, today.month - 1
    if month == 0:
        year, month = year - 1, 12
    day = min(today.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip().replace(".", "-").replace("/", "-"))
    except ValueError:
        return None


def parse_news_file(path: Path, today: date | None = None) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta: dict[str, object] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = _front_value(value)
    if meta.get("published", True) is False:
        return None
    today = today or date.today()
    raw_date = str(meta.get("date", "")).strip()
    parsed = _parse_date(raw_date)
    cutoff = _one_month_ago(today)
    title = str(meta.get("title", path.stem)).strip()
    image = str(meta.get("image", "")).strip()
    return {
        "title": title,
        "summary": str(meta.get("summary", "")).strip(),
        "date": parsed.isoformat() if parsed else raw_date,
        "dateObj": parsed,
        "slug": path.stem,
        "url": f"news/{path.stem}.html",
        "relatedUrl": str(meta.get("link", "")).strip(),
        "image": image,
        "bodyMarkdown": parts[2].lstrip("\n"),
        "isNew": bool(parsed and cutoff <= parsed <= today),
        "sourcePath": str(path),
    }


def load_news(root: Path, today: date | None = None) -> list[dict]:
    folder = root / "contents" / "news"
    if not folder.exists(): return []
    items = []
    for path in folder.glob("*.md"):
        if path.name.startswith("_") or path.name.lower() == "readme.md": continue
        item = parse_news_file(path, today=today)
        if item: items.append(item)
    items.sort(key=lambda x: (x.get("dateObj") or date.min, x.get("title", "")), reverse=True)
    return items


def legacy_news_items(data: dict) -> list[dict]:
    legacy = (data.get("news") or {}).get("items", [])
    return [{"title": item.get("text", ""), "summary": "", "date": str(item.get("date", "")).replace(".", "-"), "url": item.get("url", "") or "#", "relatedUrl": item.get("url", ""), "bodyMarkdown": "", "isNew": False, "slug": f"legacy-{i+1}"} for i, item in enumerate(legacy)]


def render_news(items: list[dict], prefix: str = "", limit: int = 3) -> str:
    rows = []
    for item in items[:limit]:
        url = local_url(item.get("url", ""), prefix)
        title = esc(item.get("title", ""))
        if url and url != "#": title = f'<a href="{esc(url)}">{title}</a>'
        new_badge = '<span class="news-new">NEW!</span>' if item.get("isNew") else ""
        display_date = str(item.get("date", "")).replace("-", ".")
        rows.append('<article class="news-item">' f'<div class="news-date"><time datetime="{esc(item.get("date", ""))}">{esc(display_date)}</time>{new_badge}</div>' f'<p>{title}</p></article>')
    return "".join(rows) or '<p class="news-empty">最新情報は準備中です。</p>'


def build_news_index(data: dict, news_items: list[dict]) -> str:
    site, p = data["site"], data["profile"]
    rows = []
    for item in news_items:
        display_date = str(item.get("date", "")).replace("-", ".")
        new_badge = '<span class="news-new">NEW!</span>' if item.get("isNew") else ""
        summary = f'<p>{esc(item.get("summary", ""))}</p>' if item.get("summary") else ""
        rows.append('<article class="news-archive-item">' f'<div class="news-archive-date"><time datetime="{esc(item.get("date", ""))}">{esc(display_date)}</time>{new_badge}</div>' f'<div><h2><a href="../{esc(item["url"])}">{esc(item.get("title", ""))}</a></h2>{summary}</div></article>')
    body = "".join(rows) or '<p class="news-empty">公開中のお知らせはありません。</p>'
    canonical = urljoin(site["url"], "news/")
    desc = f'{p["nameJa"]} / noto Lab の最新情報・お知らせ。'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>News | noto Lab</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(canonical)}">{favicon_links("../")}
{og_meta(site, "News | noto Lab", desc, canonical)}<link rel="alternate" type="application/rss+xml" title="noto Lab Feed" href="../feed.xml"><link rel="stylesheet" href="../styles.css?v=20260808i"><script src="../script.js?v=20260808i" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, prefix="../", active="home")}
<main id="main"><section class="works-hero news-hero"><div class="container"><a class="back-link" href="../index.html">← トップページへ戻る</a><p class="eyebrow">Updates</p><h1>News</h1><p>研究・発表・サイト更新などの最新情報です。</p></div></section>
<section class="news-archive"><div class="container news-archive-inner">{body}</div></section></main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''


def build_news_detail(data: dict, item: dict) -> str:
    site, p = data["site"], data["profile"]
    canonical = urljoin(site["url"], item["url"])
    display_date = str(item.get("date", "")).replace("-", ".")
    new_badge = '<span class="news-new">NEW!</span>' if item.get("isNew") else ""
    body, toc = markdown_to_html_with_toc(item.get("bodyMarkdown", ""), prefix="../")
    toc_html = ""
    if len(toc) >= 2:
        toc_html = '<nav class="article-toc" aria-label="ページ内目次"><strong>Contents</strong><ol>' + ''.join(f'<li><a href="#{esc(i)}">{esc(t)}</a></li>' for i, t in toc) + '</ol></nav>'
    related = f'<p class="news-related"><a href="{esc(item["relatedUrl"])}" target="_blank" rel="noopener noreferrer">関連ページを見る ↗</a></p>' if item.get("relatedUrl") else ""
    lead = f'<p class="article-lead">{esc(item.get("summary", ""))}</p>' if item.get("summary") else ""
    title = f'{item.get("title", "")} | News | noto Lab'
    desc = item.get("summary") or item.get("title", "")
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(canonical)}">{favicon_links("../")}
{og_meta(site, title, desc, canonical, item.get("image") or None, "article")}<link rel="alternate" type="application/rss+xml" title="noto Lab Feed" href="../feed.xml"><link rel="stylesheet" href="../styles.css?v=20260808i"><script src="../script.js?v=20260808i" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, prefix="../", active="home")}<main id="main"><article class="article-page"><div class="container article-container"><p class="breadcrumb"><a href="../index.html">Home</a> / <a href="index.html">News</a></p>
<div class="article-meta-row"><time datetime="{esc(item.get("date", ""))}">{esc(display_date)}</time>{new_badge}</div><h1>{esc(item.get("title", ""))}</h1>{lead}{toc_html}<div class="article-body">{body}{related}</div><div class="article-back"><a href="index.html">← News一覧へ戻る</a></div></div></article></main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="../index.html">トップページへ戻る ←</a></div></footer></body></html>'''
