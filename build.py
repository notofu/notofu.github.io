#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT_PATH = ROOT / "content.json"
CONTENTS_PATH = ROOT / "contents"

CONTENT_CATEGORIES = {
    "research": {"label": "研究テーマ", "badge": "Research", "class": "research", "dir": "research"},
    "graduation": {"label": "卒業研究", "badge": "Graduation", "class": "graduation", "dir": "graduation"},
    "blog": {"label": "Blog", "badge": "Blog", "class": "blog", "dir": "blog"},
}

RESEARCH_DEFAULTS = [
    {"url": "research/music-cognition.html", "image": "assets/noto-lab-icon.png", "slug": "music-cognition"},
    {"url": "research/performance.html", "image": "assets/noto-lab-icon.png", "slug": "performance"},
    {"url": "research/gaze.html", "image": "assets/noto-lab-icon.png", "slug": "gaze"},
    {"url": "research/ensemble.html", "image": "assets/noto-lab-icon.png", "slug": "ensemble"},
]

DEFAULT_NEWS = {
    "heading": "News",
    "items": [
        {"date": "2026.08.07", "text": "ウェブサイトを更新しました。", "url": ""},
        {"date": "2026.06.26", "text": "ICEC 2026 の Work in Progress が採択されました。", "url": ""},
    ],
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def is_external(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def href(url: str, label: str, class_name: str = "") -> str:
    if not url:
        return ""
    cls = f' class="{esc(class_name)}"' if class_name else ""
    extra = ' target="_blank" rel="noopener noreferrer"' if is_external(url) else ""
    return f'<a{cls} href="{esc(url)}"{extra}>{label}</a>'


def shorten(text: str, limit: int = 78) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("、。 ,") + "…"



def _front_value(value: str):
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("[") and value.endswith("]"):
        return [x.strip().strip('"\'') for x in value[1:-1].split(",") if x.strip()]
    return value


def parse_markdown_file(path: Path, category: str) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta_text, body = parts[1], parts[2].lstrip("\n")
    meta: dict[str, object] = {}
    for line in meta_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = _front_value(value)
    if meta.get("published", True) is False:
        return None
    title = str(meta.get("title", path.stem)).strip()
    summary = str(meta.get("summary", "")).strip()
    image = str(meta.get("image", "")).strip()
    thumbnail = str(meta.get("thumbnail", "")).strip()
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(",") if x.strip()]
    cat = str(meta.get("category", category)).strip().lower()
    if cat not in CONTENT_CATEGORIES:
        cat = category
    cfg = CONTENT_CATEGORIES[cat]
    fallback = not image
    if fallback:
        image = "assets/noto-lab-icon.png"
    if not thumbnail:
        thumbnail = image
    order_raw = meta.get("order", 9999)
    try:
        order = int(order_raw)
    except (TypeError, ValueError):
        order = 9999
    return {
        "title": title,
        "summary": summary,
        "description": summary,
        "image": image,
        "thumbnail": thumbnail,
        "imageAlt": str(meta.get("imageAlt", "noto Lab" if fallback else f"{title}のサムネイル")),
        "date": str(meta.get("date", "")),
        "tags": tags,
        "order": order,
        "slug": path.stem,
        "category": cat,
        "categoryLabel": cfg["label"],
        "categoryBadge": cfg["badge"],
        "categoryClass": cfg["class"],
        "url": f'{cfg["dir"]}/{path.stem}.html',
        "bodyMarkdown": body,
        "_imageFallback": fallback,
        "sourcePath": str(path.relative_to(ROOT)),
    }


def fallback_research_items(data: dict) -> list[dict]:
    items = []
    for i, raw in enumerate(data.get("research", {}).get("areas", [])):
        old = research_item_data(raw, i)
        items.append({
            "title": old["title"],
            "summary": old.get("shortDescription") or old.get("description", ""),
            "description": old.get("description", ""),
            "image": old["image"],
            "thumbnail": old.get("thumbnail") or old["image"],
            "imageAlt": old["imageAlt"],
            "date": "",
            "tags": old.get("tags", []),
            "order": i + 1,
            "slug": old["slug"],
            "category": "research",
            "categoryLabel": "研究テーマ",
            "categoryBadge": "Research",
            "categoryClass": "research",
            "url": old["url"],
            "bodyMarkdown": f'## 概要\n\n{old.get("description", "")}\n\n## 研究内容\n\n詳しい説明、図、関連論文などは順次追加予定です。',
            "_imageFallback": old.get("_imageFallback", False),
            "sourcePath": "content.json",
        })
    return items


def load_content_items(data: dict) -> list[dict]:
    items: list[dict] = []
    for category in CONTENT_CATEGORIES:
        folder = CONTENTS_PATH / category
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name.startswith("_") or path.name.lower() == "readme.md":
                continue
            item = parse_markdown_file(path, category)
            if item:
                items.append(item)
    if not any(x["category"] == "research" for x in items):
        items.extend(fallback_research_items(data))

    research = sorted([x for x in items if x["category"] == "research"], key=lambda x: (x.get("order", 9999), x.get("title", "")))
    others = []
    for category in ("graduation", "blog"):
        group = [x for x in items if x["category"] == category]
        ordered = sorted([x for x in group if x.get("order", 9999) != 9999], key=lambda x: x.get("order", 9999))
        unordered = sorted([x for x in group if x.get("order", 9999) == 9999], key=lambda x: x.get("date", ""), reverse=True)
        others.extend(ordered + unordered)
    return research + others


def local_url(url: str, prefix: str = "") -> str:
    if not url or is_external(url) or url.startswith("#") or url.startswith("mailto:"):
        return url
    return prefix + url


def inline_markdown(text: str, prefix: str = "") -> str:
    escaped = esc(text)
    def image_repl(match):
        alt, url = match.group(1), html.unescape(match.group(2))
        return f'<img class="article-inline-image" src="{esc(local_url(url, prefix))}" alt="{alt}" loading="lazy">'
    escaped = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_repl, escaped)
    def link_repl(match):
        label, url = match.group(1), html.unescape(match.group(2))
        target = ' target="_blank" rel="noopener noreferrer"' if is_external(url) else ''
        return f'<a href="{esc(local_url(url, prefix))}"{target}>{label}</a>'
    escaped = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    return escaped


def markdown_to_html(text: str, prefix: str = "") -> str:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            joined = " ".join(x.strip() for x in paragraph)
            out.append(f'<p>{inline_markdown(joined, prefix)}</p>')
            paragraph = []

    def flush_list():
        nonlocal list_type, list_items
        if list_type and list_items:
            tag = "ol" if list_type == "ol" else "ul"
            out.append(f'<{tag}>' + ''.join(f'<li>{inline_markdown(x, prefix)}</li>' for x in list_items) + f'</{tag}>')
        list_type = None
        list_items = []

    for raw in lines + [""]:
        stripped = raw.strip()
        if not stripped:
            flush_paragraph(); flush_list(); continue
        if stripped in {"---", "***"}:
            flush_paragraph(); flush_list(); out.append("<hr>"); continue
        m = re.match(r'^(#{2,4})\s+(.+)$', stripped)
        if m:
            flush_paragraph(); flush_list()
            level = len(m.group(1))
            out.append(f'<h{level}>{inline_markdown(m.group(2), prefix)}</h{level}>')
            continue
        if stripped.startswith("> "):
            flush_paragraph(); flush_list(); out.append(f'<blockquote>{inline_markdown(stripped[2:], prefix)}</blockquote>'); continue
        m = re.match(r'^[-*]\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if list_type not in {None, "ul"}: flush_list()
            list_type = "ul"; list_items.append(m.group(1)); continue
        m = re.match(r'^\d+\.\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if list_type not in {None, "ol"}: flush_list()
            list_type = "ol"; list_items.append(m.group(1)); continue
        paragraph.append(stripped)
    return "".join(out)


def render_category_badge(item: dict) -> str:
    return f'<span class="content-badge content-badge--{esc(item["categoryClass"])}"><span aria-hidden="true"></span>{esc(item["categoryBadge"])}</span>'


def render_content_cards(items: list[dict], prefix: str = "", include_category: bool = True) -> str:
    cards = []
    for item in items:
        url = local_url(item["url"], prefix)
        image = local_url(item.get("thumbnail") or item["image"], prefix)
        fallback = " research-thumb--fallback" if item.get("_imageFallback") else ""
        meta = render_category_badge(item) if include_category else ""
        if item.get("date"):
            meta += f'<time datetime="{esc(item["date"])}">{esc(item["date"].replace("-", "."))}</time>'
        cards.append(
            '<article class="research-card content-card">'
            f'<a class="research-thumb-link" href="{esc(url)}" aria-label="{esc(item["title"])}の詳細を見る">'
            f'<img class="research-thumb{fallback}" src="{esc(image)}" alt="{esc(item["imageAlt"])}" width="480" height="270" loading="lazy" decoding="async" fetchpriority="low">'
            '</a>'
            '<div class="research-card-copy">'
            f'<h3><a href="{esc(url)}">{esc(item["title"])}</a></h3>'
            f'<div class="content-card-meta">{meta}</div>'
            f'<p>{esc(shorten(item.get("summary", ""), 58))}</p>'
            '</div></article>'
        )
    return "".join(cards)


def render_content_row(category: str, items: list[dict], prefix: str = "../") -> str:
    cfg = CONTENT_CATEGORIES[category]
    cards = render_content_cards(items, prefix=prefix, include_category=True)
    if not cards:
        cards = '<div class="content-empty">現在、公開中の記事はありません。</div>'
    controls = ""
    if items:
        controls = (
            f'<div class="content-row-controls" aria-label="{esc(cfg["label"])}のスライド操作">'
            '<button type="button" data-content-prev aria-label="前へ">←</button>'
            '<button type="button" data-content-next aria-label="次へ">→</button>'
            '</div>'
        )
    return (
        f'<section class="content-row content-row--{esc(cfg["class"])}" id="{esc(category)}" data-content-row>'
        '<div class="content-row-head"><div>'
        '<span class="content-row-mark" aria-hidden="true"></span>'
        f'<h2>{esc(cfg["label"])}</h2></div>{controls}</div>'
        f'<div class="content-row-slider" data-content-slider>{cards}</div>'
        '</section>'
    )


def research_item_data(item: dict, index: int) -> dict:
    default = RESEARCH_DEFAULTS[index] if index < len(RESEARCH_DEFAULTS) else {
        "url": f"research/theme-{index + 1}.html",
        "image": "assets/noto-lab-icon.png",
        "slug": f"theme-{index + 1}",
    }
    merged = dict(item)
    if not merged.get("url"):
        merged["url"] = default["url"]
    if not merged.get("image"):
        merged["image"] = default["image"]
        merged["_imageFallback"] = True
    else:
        merged["_imageFallback"] = False
    if not merged.get("imageAlt"):
        merged["imageAlt"] = "noto Lab" if merged["_imageFallback"] else f'{item.get("title", "研究テーマ")}のサムネイル'
    if not merged.get("slug"):
        merged["slug"] = default["slug"]
    return merged

def header(profile: dict, prefix: str = "", active: str = "home") -> str:
    links = [
        ("home", f"{prefix}index.html", "Home"),
        ("research", f"{prefix}research/index.html", "Research"),
        ("publications", f"{prefix}works.html", "Publications"),
        ("teaching", f"{prefix}teaching.html", "Teaching"),
        ("profile", f"{prefix}index.html#profile", "Profile"),
    ]
    nav = "".join(
        f'<a href="{u}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, u, label in links
    )
    mobile = "".join(f'<a href="{u}">{label}</a>' for _, u, label in links)
    return f'''<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="noto Lab ホーム">
      <img class="brand-logo" src="{prefix}assets/noto-lab-wordmark.png" alt="noto Lab" width="141" height="30">
    </a>
    <nav class="desktop-nav" aria-label="主要メニュー">{nav}</nav>
    <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く"><span></span><span></span><span></span></button>
  </div>
  <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">{mobile}</nav>
</header>'''

def render_news(news: dict) -> str:
    rows = []
    for item in news.get("items", [])[:5]:
        text = esc(item.get("text", ""))
        if item.get("url"):
            text = href(item["url"], text)
        rows.append(
            '<article class="news-item">'
            f'<time>{esc(item.get("date", ""))}</time>'
            f'<p>{text}</p>'
            '</article>'
        )
    return "".join(rows) or '<p class="news-empty">最新情報は準備中です。</p>'


def render_research(items: list[dict], prefix: str = "") -> str:
    cards = []
    for i, raw in enumerate(items):
        item = research_item_data(raw, i)
        url = item["url"]
        if prefix and not is_external(url):
            url = prefix + url
        image = item["image"]
        if prefix and not is_external(image):
            image = prefix + image
        short = shorten(item.get("shortDescription") or item.get("description", ""), 52)
        fallback_class = " research-thumb--fallback" if item.get("_imageFallback") else ""
        cards.append(
            '<article class="research-card">'
            f'<a class="research-thumb-link" href="{esc(url)}" aria-label="{esc(item["title"])}の詳細を見る">'
            f'<img class="research-thumb{fallback_class}" src="{esc(image)}" alt="{esc(item["imageAlt"])}" width="720" height="405" loading="lazy">'
            '</a>'
            '<div class="research-card-copy">'
            f'<p class="research-meta">Research Theme {i+1:02d}</p>'
            f'<h3><a href="{esc(url)}">{esc(item["title"])}</a></h3>'
            f'<p>{esc(short)}</p>'
            '</div></article>'
        )
    return "".join(cards)

def publication_kind(type_text: str) -> tuple[str, str]:
    t = type_text or ""
    if ("査読論文" in t or "論文" in t or "テクニカル" in t) and "国際会議" not in t:
        return "journal", "論文"
    if "国際会議" in t:
        return "conference", "国際会議"
    if any(x in t for x in ["研究会", "学会発表", "全国大会", "発表"]):
        return "presentation", "学会発表"
    if any(x in t for x in ["紀要", "研究報告"]):
        return "report", "研究報告"
    return "other", t or "業績"


def render_selected_publications(items: list[dict]) -> str:
    rows = []
    for item in items[:4]:
        kind, label = publication_kind(item.get("type", ""))
        title = esc(item.get("title", ""))
        url = item.get("url", "")
        if url:
            title = href(url, title)
        venue = esc(item.get("venue", ""))
        rows.append(
            '<article class="publication-item">'
            f'<span class="pub-badge pub-badge--{kind}">{esc(label)}</span>'
            '<div class="publication-copy">'
            f'<h3>{title}</h3>'
            f'<p>{venue}</p>'
            '</div>'
            f'<div class="publication-year">{esc(item.get("year", ""))}</div>'
            '<div class="publication-arrow" aria-hidden="true">›</div>'
            '</article>'
        )
    return "".join(rows)


def render_teaching(items: list[dict]) -> str:
    rows = []
    for item in items[:6]:
        rows.append(
            '<article class="teaching-item">'
            f'<h3>{esc(item.get("title", ""))}</h3>'
            f'<p>{esc(shorten(item.get("description", ""), 66))}</p>'
            '</article>'
        )
    return "".join(rows)


def render_history(items: list[dict]) -> str:
    return "".join(
        '<article class="timeline-item">'
        f'<div class="timeline-period">{esc(item.get("period", ""))}</div>'
        '<div class="timeline-body">'
        f'<h3>{esc(item.get("title", ""))}</h3>'
        f'<p>{esc(item.get("detail", ""))}</p>'
        '</div></article>'
        for item in items
    )


def build_json_ld(data: dict) -> str:
    site = data["site"]
    p = data["profile"]
    same_as = [x["url"] for x in data.get("links", {}).get("items", []) if x.get("sameAs")]
    person = {
        "@type": "Person",
        "@id": urljoin(site["url"], "#person"),
        "name": p["nameJa"],
        "alternateName": p["nameEn"],
        "url": site["url"],
        "description": p["summary"],
        "jobTitle": p["position"],
        "affiliation": {"@type": "CollegeOrUniversity", "name": p["affiliationEn"], "url": "https://www.hakodate-ct.ac.jp/"},
        "knowsAbout": p.get("keywords", []),
        "sameAs": same_as,
    }
    if p.get("image"):
        person["image"] = urljoin(site["url"], p["image"])
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "url": site["url"], "name": f'{p["nameJa"]} / {p["nameEn"]}', "inLanguage": site["language"]},
            {"@type": "ProfilePage", "url": site["url"], "name": site["title"], "description": site["description"], "dateModified": date.today().isoformat(), "mainEntity": person},
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def build_home(data: dict) -> str:
    site = data["site"]
    p = data["profile"]
    research = data["research"]
    content_items = load_content_items(data)
    research_items = [x for x in content_items if x["category"] == "research"]
    outputs = data["outputs"]
    teaching = data["teaching"]
    links = data.get("links", {}).get("items", [])
    news = data.get("news") or DEFAULT_NEWS

    profile_image = ""
    if p.get("image"):
        profile_image = f'<img class="profile-photo" src="{esc(p["image"])}" alt="{esc(p.get("imageAlt", p["nameJa"]))}" width="148" height="148" fetchpriority="high">'

    external_links = "".join(
        href(x.get("url", ""), esc(x.get("label", "")) + " ↗") for x in links[:3]
    )
    facts = [
        ("所属", p.get("affiliation", "")),
        ("職位", p.get("position", "")),
        ("学位", p.get("degree", "")),
        ("拠点", p.get("location", "")),
    ]
    fact_html = "".join(f'<div class="fact-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
    og_url = urljoin(site["url"], site.get("ogImage", "assets/og-image.png"))

    return f'''<!doctype html>
<html lang="{esc(site.get("language", "ja"))}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(site["title"])}</title>
  <meta name="description" content="{esc(site["description"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{esc(site["url"])}">
  <link rel="icon" href="assets/noto-lab-icon.png" type="image/png">
  <meta property="og:type" content="profile"><meta property="og:title" content="{esc(site["title"])}"><meta property="og:description" content="{esc(site["description"])}"><meta property="og:image" content="{esc(og_url)}"><meta property="og:url" content="{esc(site["url"])}">
  <link rel="stylesheet" href="styles.css"><script src="script.js" defer></script>
  <script type="application/ld+json">{build_json_ld(data)}</script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
{header(p, active="home")}
<main id="main">
  <section class="hero" id="overview">
    <div class="container hero-grid">
      <div class="overview-lead">
        <p class="eyebrow">Music Information Processing / HCI</p>
        <h1>能登 楓 のWebページ</h1>
        <p class="overview-summary">{esc(shorten(p["summary"], 90))}</p>
        <div class="overview-actions">
          <a class="text-link" href="#research">研究テーマを見る ↓</a>
          <a class="text-link" href="works.html">研究業績を見る →</a>
        </div>
      </div>
      <section class="news-panel" id="news" aria-labelledby="news-title">
        <div class="section-mini-head"><h2 id="news-title">{esc(news.get("heading", "News"))}</h2></div>
        <div class="news-list">{render_news(news)}</div>
      </section>
    </div>
  </section>

  <section class="research-overview" id="research">
    <div class="container">
      <div class="section-title-row">
        <h2><a class="section-title-link" href="research/index.html">Research Themes</a></h2>
        <div class="research-heading-actions">
          <div class="research-controls" aria-label="研究テーマのスライド操作">
            <button type="button" data-research-prev aria-label="前の研究テーマ">←</button>
            <button type="button" data-research-next aria-label="次の研究テーマ">→</button>
          </div>
          <a href="research/index.html">すべての研究を見る →</a>
        </div>
      </div>
      <div class="research-slider" data-research-slider>
        {render_content_cards(research_items, include_category=False)}
      </div>
    </div>
  </section>

  <section class="overview-bottom">
    <div class="container overview-columns">
      <section class="overview-block" id="publications">
        <div class="section-mini-head"><h2>Selected Publications</h2><a href="works.html">すべての業績を見る →</a></div>
        <div class="publication-list">{render_selected_publications(outputs.get("items", []))}</div>
      </section>
      <section class="overview-block" id="teaching">
        <div class="section-mini-head"><h2>Teaching</h2><a href="teaching.html">すべて見る →</a></div>
        <div class="teaching-list">{render_teaching(teaching.get("items", []))}</div>
      </section>
    </div>
  </section>

  <section class="profile-section" id="profile">
    <div class="container profile-identity">
      <div class="profile-identity-main">
        {profile_image}
        <div>
          <p class="eyebrow">Profile</p>
          <h2>{esc(p["nameJa"])} <span>{esc(p["nameEn"])}</span></h2>
          <p class="profile-affiliation">{esc(p["affiliation"])}　{esc(p["position"])}</p>
          <div class="profile-links">{external_links}</div>
        </div>
      </div>
    </div>
    <div class="container profile-section-grid">
      <div>
        <h3>Information</h3>
        <dl class="fact-list">{fact_html}</dl>
      </div>
      <div>
        <h3>Career</h3>
        <div>{render_history(p.get("history", []))}</div>
      </div>
    </div>
  </section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''



def build_content_detail(data: dict, item: dict) -> str:
    site = data["site"]
    p = data["profile"]
    image = local_url(item["image"], "../")
    fallback_class = " detail-thumb--fallback" if item.get("_imageFallback") else ""
    tags = ''.join(f'<span>{esc(tag)}</span>' for tag in item.get("tags", []))
    date_html = f'<time datetime="{esc(item["date"])}">{esc(item["date"].replace("-", "."))}</time>' if item.get("date") else ''
    canonical = urljoin(site["url"], item["url"])
    body = markdown_to_html(item.get("bodyMarkdown", ""), prefix="../")
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(item["title"])} | noto Lab</title>
  <meta name="description" content="{esc(item.get("summary", ""))}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="../assets/noto-lab-icon.png" type="image/png">
  <link rel="stylesheet" href="../styles.css"><script src="../script.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
{header(p, prefix="../", active="research")}
<main id="main">
  <article class="article-page">
    <div class="container article-container">
      <p class="breadcrumb"><a href="../index.html">Home</a> / <a href="../research/index.html">Research</a> / {esc(item["categoryLabel"])}</p>
      <div class="article-meta-row">{render_category_badge(item)}{date_html}</div>
      <h1>{esc(item["title"])}</h1>
      <p class="article-lead">{esc(item.get("summary", ""))}</p>
      <div class="article-hero-image{fallback_class}"><img src="{esc(image)}" alt="{esc(item["imageAlt"])}"></div>
      <div class="article-tags">{tags}</div>
      <div class="article-body">{body}</div>
      <div class="article-back"><a href="../research/index.html">← Research一覧へ戻る</a></div>
    </div>
  </article>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''


def build_research_index(data: dict, content_items: list[dict]) -> str:
    p = data["profile"]
    groups = {category: [x for x in content_items if x["category"] == category] for category in CONTENT_CATEGORIES}
    rows = ''.join(render_content_row(category, groups[category], prefix="../") for category in ("research", "graduation", "blog"))
    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research | noto Lab</title>
  <meta name="description" content="研究テーマ、卒業研究、Blogの記事一覧です。">
  <link rel="icon" href="../assets/noto-lab-icon.png" type="image/png">
  <link rel="stylesheet" href="../styles.css"><script src="../script.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
{header(p, prefix="../", active="research")}
<main id="main">
  <section class="works-hero content-hub-hero"><div class="container"><a class="back-link" href="../index.html">← トップページへ戻る</a><p class="eyebrow">noto Lab</p><h1>Research</h1><p>研究テーマ、卒業研究、Blogをまとめています。気になる項目から詳細をご覧ください。</p><nav class="content-filter-nav" aria-label="Researchカテゴリ"><a href="#research">研究テーマ</a><a href="#graduation">卒業研究</a><a href="#blog">Blog</a></nav></div></section>
  <section class="content-hub"><div class="container">{rows}</div></section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''


def render_teaching_fallback(items: list[dict]) -> str:
    """Static fallback shown until the public researchmap API finishes loading."""
    rows = []
    for item in items:
        rows.append(
            '<article class="teaching-course teaching-course--fallback">'
            '<div class="teaching-course-period">掲載中</div>'
            '<div class="teaching-course-main">'
            f'<h2>{esc(item.get("title", ""))}</h2>'
            f'<p class="teaching-course-description">{esc(item.get("description", ""))}</p>'
            '</div></article>'
        )
    return "".join(rows)


def build_teaching_page(data: dict) -> str:
    site = data["site"]
    p = data["profile"]
    teaching = data.get("teaching", {})
    fallback = render_teaching_fallback(teaching.get("items", []))
    canonical = urljoin(site["url"], "teaching.html")
    rmap_url = "https://researchmap.jp/notokaede/teaching_experience"

    return f'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Teaching | {esc(p["nameJa"])} / {esc(p["nameEn"])}</title>
  <meta name="description" content="{esc(p["nameJa"])}の担当経験のある科目・教育活動。Researchmapの公開情報をもとに表示しています。">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="assets/noto-lab-icon.png" type="image/png">
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
{header(p, active="teaching")}
<main id="main">
  <section class="works-hero teaching-hero">
    <div class="container">
      <a class="back-link" href="index.html">← トップページへ戻る</a>
      <p class="eyebrow">Education</p>
      <h1>Teaching</h1>
      <p>担当経験のある科目・教育活動を掲載しています。公開されているResearchmapの情報を自動取得して表示します。</p>
      <div class="teaching-source-row">
        <span class="teaching-live-status" data-rmap-status>Researchmapを読み込み中…</span>
        <a href="{rmap_url}" target="_blank" rel="noopener noreferrer">Researchmapで確認する ↗</a>
      </div>
    </div>
  </section>

  <section class="teaching-page-section">
    <div class="container teaching-page-grid">
      <aside class="teaching-page-aside" aria-label="Teachingページの説明">
        <p class="section-label">COURSES</p>
        <h2>担当科目</h2>
        <p>科目名、担当機関、担当期間をResearchmapの公開データから表示します。</p>
      </aside>

      <div class="teaching-course-list" data-researchmap-teaching data-permalink="notokaede">
        {fallback}
      </div>
    </div>
  </section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="index.html">トップページへ戻る ←</a></div></footer>
</body>
</html>'''

def update_works_header(text: str, p: dict) -> str:
    # Replace only the existing header so publication data remains untouched.
    start = text.find('<header class="site-header"')
    end = text.find('</header>', start)
    if start != -1 and end != -1:
        text = text[:start] + header(p, active="publications") + text[end + len('</header>'):]
    return text


def main() -> None:
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for name in ["styles.css", "script.js", ".nojekyll"]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, DIST / name)
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", DIST / "assets")

    (DIST / "index.html").write_text(build_home(data), encoding="utf-8")

    (DIST / "teaching.html").write_text(build_teaching_page(data), encoding="utf-8")

    works = ROOT / "works.html"
    if works.exists():
        works_text = update_works_header(works.read_text(encoding="utf-8"), data["profile"])
        (DIST / "works.html").write_text(works_text, encoding="utf-8")

    content_items = load_content_items(data)
    rdir = DIST / "research"
    rdir.mkdir(exist_ok=True)
    (rdir / "index.html").write_text(build_research_index(data, content_items), encoding="utf-8")

    for category in ("research", "graduation", "blog"):
        out_dir = DIST / CONTENT_CATEGORIES[category]["dir"]
        out_dir.mkdir(exist_ok=True)
    for item in content_items:
        target = DIST / item["url"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_content_detail(data, item), encoding="utf-8")

    site_url = data["site"]["url"].rstrip("/") + "/"
    urls = [site_url, urljoin(site_url, "works.html"), urljoin(site_url, "teaching.html"), urljoin(site_url, "research/")]
    urls.extend(urljoin(site_url, item["url"]) for item in content_items)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{esc(u)}</loc></url>\n' for u in urls) + '</urlset>\n'
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, "sitemap.xml")}\n', encoding="utf-8")


if __name__ == "__main__":
    main()
