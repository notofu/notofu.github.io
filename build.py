#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT_PATH = ROOT / "content.json"

RESEARCH_DEFAULTS = [
    {"url": "research/music-cognition.html", "image": "assets/research-preparing-01.png", "slug": "music-cognition"},
    {"url": "research/performance.html", "image": "assets/research-preparing-02.png", "slug": "performance"},
    {"url": "research/gaze.html", "image": "assets/research-preparing-03.png", "slug": "gaze"},
    {"url": "research/ensemble.html", "image": "assets/research-preparing-04.png", "slug": "ensemble"},
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


def research_item_data(item: dict, index: int) -> dict:
    default = RESEARCH_DEFAULTS[index] if index < len(RESEARCH_DEFAULTS) else {
        "url": f"research/theme-{index + 1}.html",
        "image": "assets/research-preparing-01.png",
        "slug": f"theme-{index + 1}",
    }
    merged = dict(item)
    merged.setdefault("url", default["url"])
    merged.setdefault("image", default["image"])
    merged.setdefault("imageAlt", f'{item.get("title", "研究テーマ")}のサムネイル（画像準備中）')
    merged.setdefault("slug", default["slug"])
    return merged


def header(profile: dict, prefix: str = "", active: str = "home") -> str:
    links = [
        ("home", f"{prefix}index.html", "Home"),
        ("research", f"{prefix}index.html#research", "Research"),
        ("publications", f"{prefix}works.html", "Publications"),
        ("teaching", f"{prefix}index.html#teaching", "Teaching"),
        ("profile", f"{prefix}index.html#profile", "Profile"),
    ]
    nav = "".join(
        f'<a href="{u}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, u, label in links
    )
    mobile = "".join(f'<a href="{u}">{label}</a>' for _, u, label in links)
    return f'''<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html">{esc(profile["nameJa"])} <small>{esc(profile["nameEn"])}</small></a>
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
        short = shorten(item.get("shortDescription") or item.get("description", ""), 72)
        cards.append(
            '<article class="research-card">'
            f'<a class="research-thumb-link" href="{esc(url)}" aria-label="{esc(item["title"])}の詳細を見る">'
            f'<img class="research-thumb" src="{esc(image)}" alt="{esc(item["imageAlt"])}" width="720" height="510" loading="lazy">'
            '</a>'
            '<div class="research-card-copy">'
            f'<div class="research-number">{i+1:02d}</div>'
            '<div>'
            f'<h3><a href="{esc(url)}">{esc(item["title"])}</a></h3>'
            f'<p>{esc(short)}</p>'
            '</div></div></article>'
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
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <meta property="og:type" content="profile"><meta property="og:title" content="{esc(site["title"])}"><meta property="og:description" content="{esc(site["description"])}"><meta property="og:image" content="{esc(og_url)}"><meta property="og:url" content="{esc(site["url"])}">
  <link rel="stylesheet" href="styles.css"><script src="script.js" defer></script>
  <script type="application/ld+json">{build_json_ld(data)}</script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
{header(p, active="home")}
<main id="main">
  <section class="hero" id="profile-top">
    <div class="container hero-grid">
      <div class="profile-panel">
        {profile_image}
        <div class="profile-copy">
          <h1>{esc(p["nameJa"])}</h1>
          <p class="name-en">{esc(p["nameEn"])}</p>
          <p class="affiliation">{esc(p["affiliation"])}　{esc(p["position"])}</p>
          <p class="profile-short">{esc(shorten(p["summary"], 100))}</p>
          <div class="profile-links">{external_links}</div>
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
      <div class="section-title-row"><h2>Research Themes</h2><a href="research/index.html">すべての研究を見る →</a></div>
      <div class="research-grid">{render_research(research.get("areas", []))}</div>
    </div>
  </section>

  <section class="overview-bottom">
    <div class="container overview-columns">
      <section class="overview-block" id="publications">
        <div class="section-mini-head"><h2>Selected Publications</h2><a href="works.html">すべての業績を見る →</a></div>
        <div class="publication-list">{render_selected_publications(outputs.get("items", []))}</div>
      </section>
      <section class="overview-block" id="teaching">
        <div class="section-mini-head"><h2>Teaching</h2></div>
        <div class="teaching-list">{render_teaching(teaching.get("items", []))}</div>
      </section>
    </div>
  </section>

  <section class="profile-section" id="profile">
    <div class="container profile-section-grid">
      <div>
        <h2>Profile</h2>
        <dl class="fact-list">{fact_html}</dl>
        <div class="link-list">{external_links}</div>
      </div>
      <div>
        <h2>Career</h2>
        <div>{render_history(p.get("history", []))}</div>
      </div>
    </div>
  </section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''


def detail_body(item: dict) -> str:
    details = item.get("details") or item.get("detail") or []
    if isinstance(details, str):
        details = [details]
    if details:
        return "".join(f'<p>{esc(x)}</p>' for x in details)
    return (
        f'<p>{esc(item.get("description", ""))}</p>'
        '<div class="preparing-note">この研究テーマの詳しい説明、図、関連論文などは順次追加予定です。</div>'
    )


def build_research_detail(data: dict, raw: dict, index: int) -> str:
    p = data["profile"]
    item = research_item_data(raw, index)
    image = "../" + item["image"] if not is_external(item["image"]) else item["image"]
    tags = "".join(f'<span>{esc(t)}</span>' for t in item.get("tags", []))
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(item["title"])} | {esc(p["nameJa"])}</title><meta name="description" content="{esc(item.get("description", ""))}"><link rel="stylesheet" href="../styles.css"><script src="../script.js" defer></script></head><body>
{header(p, prefix="../", active="research")}
<main><section class="detail-hero"><div class="container"><p class="breadcrumb"><a href="../index.html">Home</a> / <a href="index.html">Research</a> / {esc(item["title"])}</p><div class="detail-layout"><div class="detail-copy"><h1>{esc(item["title"])}</h1><p class="lead">{esc(item.get("description", ""))}</p><div class="detail-tags">{tags}</div></div><img class="detail-thumb" src="{esc(image)}" alt="{esc(item["imageAlt"])}"></div></div></section><section class="detail-body"><div class="container detail-body-inner"><h2>研究内容</h2>{detail_body(item)}</div></section></main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="../index.html#research">研究テーマ一覧へ戻る ←</a></div></footer></body></html>'''


def build_research_index(data: dict) -> str:
    p = data["profile"]
    research = data["research"]
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>研究テーマ | {esc(p["nameJa"])}</title><meta name="description" content="{esc(research.get("intro", "研究テーマ一覧"))}"><link rel="stylesheet" href="../styles.css"><script src="../script.js" defer></script></head><body>{header(p, prefix="../", active="research")}<main><section class="works-hero"><div class="container"><a class="back-link" href="../index.html">← トップページへ戻る</a><h1>Research Themes</h1><p>{esc(research.get("intro", ""))}</p></div></section><section class="research-overview"><div class="container"><div class="research-grid">{render_research(research.get("areas", []), prefix="../")}</div></div></section></main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''


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

    works = ROOT / "works.html"
    if works.exists():
        works_text = update_works_header(works.read_text(encoding="utf-8"), data["profile"])
        (DIST / "works.html").write_text(works_text, encoding="utf-8")

    rdir = DIST / "research"
    rdir.mkdir(exist_ok=True)
    (rdir / "index.html").write_text(build_research_index(data), encoding="utf-8")
    for i, raw in enumerate(data["research"].get("areas", [])):
        item = research_item_data(raw, i)
        (rdir / f'{item["slug"]}.html').write_text(build_research_detail(data, raw, i), encoding="utf-8")

    site_url = data["site"]["url"].rstrip("/") + "/"
    urls = [site_url, urljoin(site_url, "works.html"), urljoin(site_url, "research/")]
    for i, raw in enumerate(data["research"].get("areas", [])):
        urls.append(urljoin(site_url, research_item_data(raw, i)["url"]))
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{esc(u)}</loc></url>\n' for u in urls) + '</urlset>\n'
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, "sitemap.xml")}\n', encoding="utf-8")


if __name__ == "__main__":
    main()
