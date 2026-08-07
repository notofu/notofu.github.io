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
        {"date": "2026.08.07", "text": "ウェブサイトを更新しました。", "url": ""}
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


def render_research(items: list[dict]) -> str:
    cards = []
    for i, raw in enumerate(items):
        item = research_item_data(raw, i)
        url = item["url"]
        image = item["image"]
        tags = item.get("tags", [])
        short = item.get("shortDescription") or item.get("description", "")
        # トップは一覧性優先。長い説明は1文程度に抑える。
        if len(short) > 92:
            short = short[:89].rstrip("、。 ") + "…"
        tag_html = ""
        if tags:
            tag_html = '<p class="research-keywords">' + " / ".join(esc(t) for t in tags[:3]) + "</p>"
        cards.append(
            '<article class="research-card">'
            f'<a class="research-thumb-link" href="{esc(url)}" aria-label="{esc(item["title"])}の詳細を見る">'
            f'<img class="research-thumb" src="{esc(image)}" alt="{esc(item["imageAlt"])}" width="720" height="520" loading="lazy">'
            '</a>'
            '<div class="research-card-copy">'
            f'<div class="research-number">{i + 1:02d}</div>'
            '<div>'
            f'<h3><a href="{esc(url)}">{esc(item["title"])}</a></h3>'
            f'<p>{esc(short)}</p>'
            f'{tag_html}'
            f'<a class="research-more" href="{esc(url)}">詳しく見る <span aria-hidden="true">→</span></a>'
            '</div></div></article>'
        )
    return "".join(cards)


def render_news(news: dict) -> str:
    items = news.get("items", [])[:3]
    if not items:
        return '<p class="news-empty">最新情報は準備中です。</p>'
    rows = []
    for item in items:
        text = esc(item.get("text", ""))
        url = item.get("url", "")
        if url:
            text = href(url, text)
        rows.append(
            '<article class="news-item">'
            f'<time datetime="{esc(item.get("date", ""))}">{esc(item.get("date", ""))}</time>'
            f'<p>{text}</p>'
            '</article>'
        )
    return "".join(rows)


def render_projects(items: list[dict]) -> str:
    rows = []
    for item in items[:3]:
        rows.append(
            '<article class="plain-row">'
            f'<div class="plain-meta">{esc(item["period"])}</div>'
            '<div class="plain-main">'
            f'<h3>{esc(item["title"])}</h3>'
            f'{href(item.get("url", ""), "詳細を見る ↗", "text-link")}'
            '</div></article>'
        )
    return "".join(rows)


def render_outputs(items: list[dict]) -> str:
    rows = []
    for item in items[:4]:
        title = esc(item["title"])
        if item.get("url"):
            title = href(item["url"], title)
        meta = " / ".join(esc(x) for x in [item.get("venue", ""), item.get("authors", "")] if x)
        rows.append(
            '<article class="output-row">'
            f'<div class="output-year">{esc(item["year"])}</div>'
            f'<div class="output-type">{esc(item["type"])}</div>'
            '<div class="output-content">'
            f'<h3>{title}</h3>'
            f'<p>{meta}</p>'
            '</div></article>'
        )
    return "".join(rows)


def render_teaching(items: list[dict]) -> str:
    return "".join(
        '<article class="teaching-item">'
        f'<h3>{esc(item["title"])}</h3>'
        '</article>'
        for item in items[:6]
    )


def render_history(items: list[dict]) -> str:
    return "".join(
        '<article class="timeline-item">'
        f'<div class="timeline-period">{esc(item["period"])}</div>'
        '<div class="timeline-body">'
        f'<h3>{esc(item["title"])}</h3>'
        f'<p>{esc(item["detail"])}</p>'
        '</div></article>'
        for item in items
    )


def render_links(items: list[dict]) -> str:
    rows = []
    for item in items:
        extra = ' target="_blank" rel="noopener noreferrer"' if is_external(item["url"]) else ""
        rows.append(
            f'<a class="link-row" href="{esc(item["url"])}"{extra}>'
            '<span class="link-copy">'
            f'<strong>{esc(item["label"])}</strong>'
            f'<small>{esc(item["description"])}</small>'
            '</span><span class="link-arrow" aria-hidden="true">↗</span></a>'
        )
    return "".join(rows)


def build_json_ld(data: dict) -> str:
    site = data["site"]
    p = data["profile"]
    same_as = [x["url"] for x in data["links"]["items"] if x.get("sameAs")]
    person = {
        "@type": "Person",
        "@id": urljoin(site["url"], "#person"),
        "name": p["nameJa"],
        "alternateName": p["nameEn"],
        "url": site["url"],
        "description": p["summary"],
        "jobTitle": p["position"],
        "affiliation": {"@type": "CollegeOrUniversity", "name": p["affiliationEn"], "url": "https://www.hakodate-ct.ac.jp/"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Future University Hakodate", "url": "https://www.fun.ac.jp/"},
        "knowsAbout": p["keywords"],
        "sameAs": same_as,
    }
    if p.get("image"):
        person["image"] = urljoin(site["url"], p["image"])
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": urljoin(site["url"], "#website"), "url": site["url"], "name": f'{p["nameJa"]} / {p["nameEn"]}', "inLanguage": site["language"], "publisher": {"@id": person["@id"]}},
            {"@type": "ProfilePage", "@id": urljoin(site["url"], "#profile-page"), "url": site["url"], "name": site["title"], "description": site["description"], "inLanguage": site["language"], "mainEntity": {"@id": person["@id"]}, "dateModified": date.today().isoformat()},
            person,
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def header(p: dict, prefix: str = "") -> str:
    return f'''<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html">{esc(p["nameJa"])} <small>{esc(p["nameEn"])}</small></a>
    <nav class="desktop-nav" aria-label="主要メニュー">
      <a href="{prefix}index.html#news">News</a><a href="{prefix}index.html#research">Research</a><a href="{prefix}works.html">Publications</a><a href="{prefix}index.html#teaching">Teaching</a><a href="{prefix}index.html#profile">Profile</a>
    </nav>
    <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く"><span></span><span></span><span></span></button>
  </div>
  <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">
    <a href="{prefix}index.html#news">News</a><a href="{prefix}index.html#research">Research</a><a href="{prefix}works.html">Publications</a><a href="{prefix}index.html#teaching">Teaching</a><a href="{prefix}index.html#profile">Profile</a>
  </nav>
</header>'''


def build_html(data: dict) -> str:
    site, p = data["site"], data["profile"]
    research, projects, outputs = data["research"], data["projects"], data["outputs"]
    teaching, links = data["teaching"], data["links"]
    news = data.get("news") or DEFAULT_NEWS
    profile_image = ""
    if p.get("image"):
        profile_image = f'<img class="profile-photo" src="{esc(p["image"])}" alt="{esc(p["imageAlt"])}" width="84" height="84" fetchpriority="high">'
    facts = [("所属", p["affiliation"]), ("職位", p["position"]), ("学位", p["degree"]), ("拠点", p["location"])]
    facts_html = "".join(f'<div class="fact-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
    verification = site.get("googleSiteVerification", "").strip()
    verify_meta = f'<meta name="google-site-verification" content="{esc(verification)}">' if verification else ""
    rm_url = next((x["url"] for x in links["items"] if x["label"].lower() == "researchmap"), "")
    og_url = urljoin(site["url"], site["ogImage"])

    return f'''<!doctype html>
<html lang="{esc(site["language"])}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(site["title"])}</title><meta name="description" content="{esc(site["description"])}"><meta name="author" content="{esc(p["nameJa"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><meta name="theme-color" content="{esc(site["themeColor"])}">{verify_meta}
  <link rel="canonical" href="{esc(site["url"])}"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <meta property="og:type" content="profile"><meta property="og:locale" content="ja_JP"><meta property="og:title" content="{esc(site["title"])}"><meta property="og:description" content="{esc(site["description"])}"><meta property="og:url" content="{esc(site["url"])}"><meta property="og:image" content="{esc(og_url)}"><meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{build_json_ld(data)}</script>
  <link rel="stylesheet" href="styles.css"><script src="script.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p)}
<main id="main">
<section class="hero"><div class="container hero-grid">
  <div class="hero-profile">
    <div class="profile-intro">{profile_image}<div class="profile-copy"><h1>{esc(p["nameJa"])}</h1><p class="profile-name-en">{esc(p["nameEn"])}</p><p class="profile-role">{esc(p["position"])} / {esc(p["affiliation"])}</p></div></div>
    <p class="hero-summary">{esc(p["summary"])}</p>
    <div class="hero-links"><a href="#research">研究テーマを見る →</a>{href(outputs["allWorksUrl"], "研究業績を見る →")}{href(rm_url, "Researchmap ↗")}</div>
  </div>
  <aside class="news-panel" id="news" aria-labelledby="news-title"><div class="news-heading"><h2 id="news-title">{esc(news.get("heading", "News"))}</h2><span>最新情報</span></div><div class="news-list">{render_news(news)}</div></aside>
</div></section>

<section class="section research-section" id="research" aria-labelledby="research-title"><div class="container">
  <div class="section-heading"><div><p class="section-label">RESEARCH</p><h2 id="research-title">{esc(research["heading"])}</h2></div><p class="section-intro">研究テーマを選ぶと、概要・背景・関連業績をまとめたページへ移動します。</p></div>
  <div class="research-grid">{render_research(research["areas"])}</div>
</div></section>

<section class="section split-section" id="outputs" aria-labelledby="outputs-title"><div class="container split-grid">
  <div><div class="compact-heading"><p class="section-label">SELECTED PUBLICATIONS</p><h2 id="outputs-title">{esc(outputs["heading"])}</h2></div><div class="output-list">{render_outputs(outputs["items"])}</div><p class="section-more">{href(outputs["allWorksUrl"], "すべての研究業績を見る →")}</p></div>
  <div id="teaching"><div class="compact-heading"><p class="section-label">TEACHING</p><h2>{esc(teaching["heading"])}</h2></div><div class="teaching-list">{render_teaching(teaching["items"])}</div></div>
</div></section>

<section class="section" id="projects"><div class="container"><div class="section-heading"><div><p class="section-label">PROJECTS</p><h2>{esc(projects["heading"])}</h2></div><p class="section-intro">現在進行中・継続中の研究プロジェクト。</p></div><div class="plain-list">{render_projects(projects["items"])}</div></div></section>

<section class="section" id="profile"><div class="container"><div class="section-heading"><div><p class="section-label">PROFILE</p><h2>プロフィール</h2></div><p class="section-intro">所属・学位・略歴。</p></div><div class="profile-layout"><dl class="fact-list">{facts_html}</dl><div class="timeline">{render_history(p["history"])}</div></div></div></section>

<section class="section" id="links"><div class="container"><div class="section-heading"><div><p class="section-label">LINKS</p><h2>{esc(links["heading"])}</h2></div><p class="section-intro">{esc(links["text"])}</p></div><div class="link-list">{render_links(links["items"])}</div></div></section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''


def build_research_page(data: dict, raw: dict, index: int) -> tuple[str, str]:
    p = data["profile"]
    site = data["site"]
    item = research_item_data(raw, index)
    url = item["url"]
    tags = item.get("tags", [])
    tags_html = "".join(f'<li>{esc(t)}</li>' for t in tags)
    title = item["title"]
    canonical = urljoin(site["url"], url)
    return url, f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | {esc(p["nameJa"])}</title><meta name="description" content="{esc(item["description"])}"><link rel="canonical" href="{esc(canonical)}"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../styles.css"><script src="../script.js" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, "../")}
<main id="main"><section class="research-detail-hero"><div class="container"><a class="back-link" href="../index.html#research">← 研究テーマ一覧へ戻る</a><div class="research-detail-grid"><div><p class="section-label">RESEARCH THEME {index + 1:02d}</p><h1>{esc(title)}</h1><p class="research-lead">{esc(item["description"])}</p><ul class="detail-tags">{tags_html}</ul></div><img class="research-detail-image" src="../{esc(item["image"])}" alt="{esc(item["imageAlt"])}" width="720" height="520"></div></div></section>
<section class="section"><div class="container detail-content"><div><p class="section-label">OVERVIEW</p><h2>研究概要</h2></div><div><p>{esc(item["description"])}</p><div class="preparing-note"><strong>詳細説明を準備中です。</strong><p>研究の背景、分析方法、主な結果、関連データをこのページに順次追加します。</p></div></div></div></section>
<section class="section"><div class="container detail-content"><div><p class="section-label">PUBLICATIONS</p><h2>関連業績</h2></div><div><p>関連する論文・発表は研究業績ページから確認できます。</p><p><a class="text-link" href="../works.html">研究業績を見る →</a></p></div></div></section></main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="../index.html">トップページへ戻る →</a></div></footer></body></html>'''


def build_404(data: dict) -> str:
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>ページが見つかりません</title><link rel="stylesheet" href="styles.css"></head><body><main class="error-page"><div><p class="section-label">404</p><h1>ページが見つかりません</h1><p>URLをご確認ください。</p><a href="{esc(data["site"]["url"])}">トップページへ戻る →</a></div></main></body></html>'''


def main() -> None:
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    (DIST / "index.html").write_text(build_html(data), encoding="utf-8")
    (DIST / "404.html").write_text(build_404(data), encoding="utf-8")
    for name in ("styles.css", "script.js", "works.html", ".nojekyll"):
        shutil.copy2(ROOT / name, DIST / name)
    shutil.copytree(ROOT / "assets", DIST / "assets")

    research_urls = []
    for i, raw in enumerate(data["research"]["areas"]):
        rel, page = build_research_page(data, raw, i)
        out = DIST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        research_urls.append(urljoin(data["site"]["url"], rel))

    site_url = data["site"]["url"]
    urls = [site_url, urljoin(site_url, "works.html"), *research_urls]
    today = date.today().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{esc(u)}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n'
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, "sitemap.xml")}\n', encoding="utf-8")
    print(f"Built site at: {DIST}")


if __name__ == "__main__":
    main()
