#!/usr/bin/env python3
"""Build the research profile site from content.json using only Python stdlib."""

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


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def safe_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Only http/https URLs are allowed: {value}")
    return value


def external_link(url: str, label: str, class_name: str = "") -> str:
    if not url:
        return ""
    safe_url(url)
    cls = f' class="{esc(class_name)}"' if class_name else ""
    return f'<a{cls} href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'


def render_tags(tags: list[str], class_name: str = "tag-list") -> str:
    if not tags:
        return ""
    items = "".join(f"<li>{esc(tag)}</li>" for tag in tags)
    return f'<ul class="{esc(class_name)}">{items}</ul>'


def render_history(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        rows.append(
            '<div class="history-item">'
            f'<div class="history-period">{esc(item["period"])}</div>'
            '<div>'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["detail"])}</p>'
            '</div></div>'
        )
    return "".join(rows)


def render_research(items: list[dict]) -> str:
    cards = []
    for item in items:
        cards.append(
            '<article class="card">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{render_tags(item.get("tags", []))}'
            '</article>'
        )
    return "".join(cards)


def render_projects(items: list[dict]) -> str:
    cards = []
    for item in items:
        link = external_link(item.get("url", ""), "詳細を見る ↗", "card-link")
        cards.append(
            '<article class="card">'
            f'<span class="period">{esc(item["period"])}</span>'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{link}'
            '</article>'
        )
    return "".join(cards)


def render_outputs(items: list[dict]) -> str:
    rows = []
    for item in items:
        title = esc(item["title"])
        if item.get("url"):
            title = external_link(item["url"], title)
        venue = f'{esc(item["venue"])} / ' if item.get("venue") else ""
        rows.append(
            '<article class="output">'
            f'<div class="output-year">{esc(item["year"])}</div>'
            '<div>'
            f'<div class="output-type">{esc(item["type"])}</div>'
            f'<h3>{title}</h3>'
            f'<p>{venue}{esc(item["authors"])}</p>'
            '</div></article>'
        )
    return "".join(rows)


def render_teaching(items: list[dict]) -> str:
    cards = []
    for item in items:
        cards.append(
            '<article class="card">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            '</article>'
        )
    return "".join(cards)


def render_links(items: list[dict]) -> str:
    cards = []
    for item in items:
        url = safe_url(item["url"])
        cards.append(
            f'<a class="link-card" href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
            f'<strong>{esc(item["label"])} ↗</strong>'
            f'<span>{esc(item["description"])}</span>'
            '</a>'
        )
    return "".join(cards)


def build_json_ld(data: dict) -> str:
    site = data["site"]
    profile = data["profile"]
    same_as = [item["url"] for item in data["links"]["items"] if item.get("sameAs", False)]
    image_url = urljoin(site["url"], profile["image"])

    person_id = urljoin(site["url"], "#person")
    page_id = urljoin(site["url"], "#profile-page")
    website_id = urljoin(site["url"], "#website")

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": website_id,
                "url": site["url"],
                "name": f'{profile["nameJa"]} / {profile["nameEn"]}',
                "inLanguage": site["language"],
                "publisher": {"@id": person_id},
            },
            {
                "@type": "ProfilePage",
                "@id": page_id,
                "url": site["url"],
                "name": site["title"],
                "description": site["description"],
                "inLanguage": site["language"],
                "isPartOf": {"@id": website_id},
                "mainEntity": {"@id": person_id},
                "dateModified": date.today().isoformat(),
            },
            {
                "@type": "Person",
                "@id": person_id,
                "name": profile["nameJa"],
                "alternateName": profile["nameEn"],
                "url": site["url"],
                "image": image_url,
                "description": profile["summary"],
                "jobTitle": profile["position"],
                "affiliation": {
                    "@type": "CollegeOrUniversity",
                    "name": profile["affiliationEn"],
                    "url": "https://www.hakodate-ct.ac.jp/",
                },
                "alumniOf": {
                    "@type": "CollegeOrUniversity",
                    "name": "Future University Hakodate",
                    "url": "https://www.fun.ac.jp/",
                },
                "knowsAbout": profile["keywords"],
                "sameAs": same_as,
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def build_html(data: dict) -> str:
    site = data["site"]
    profile = data["profile"]
    about = data["about"]
    research = data["research"]
    projects = data["projects"]
    outputs = data["outputs"]
    teaching = data["teaching"]
    links = data["links"]

    site_url = safe_url(site["url"])
    og_url = urljoin(site_url, site["ogImage"])
    profile_image = profile.get("image", "")
    profile_image_html = ""
    if profile_image:
        profile_image_html = (
            f'<img class="profile-photo" src="{esc(profile_image)}" '
            f'alt="{esc(profile["imageAlt"])}" width="112" height="112" fetchpriority="high">'
        )

    facts = [
        ("所属", profile["affiliation"]),
        ("職位", profile["position"]),
        ("学位", profile["degree"]),
        ("拠点", profile["location"]),
    ]
    fact_html = "".join(
        f'<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>' for label, value in facts
    )
    about_html = "".join(f"<p>{esc(p)}</p>" for p in about["paragraphs"])
    json_ld = build_json_ld(data)
    verification = site.get("googleSiteVerification", "").strip()
    verification_meta = (
        f'<meta name="google-site-verification" content="{esc(verification)}">'
        if verification else ""
    )

    return f'''<!doctype html>
<html lang="{esc(site["language"])}" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(site["title"])}</title>
  <meta name="description" content="{esc(site["description"])}">
  <meta name="author" content="{esc(profile["nameJa"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
  <meta name="theme-color" content="{esc(site["themeColor"])}">
  {verification_meta}
  <link rel="canonical" href="{esc(site_url)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="sitemap" type="application/xml" href="{esc(urljoin(site_url, 'sitemap.xml'))}">

  <meta property="og:type" content="profile">
  <meta property="og:locale" content="ja_JP">
  <meta property="og:site_name" content="{esc(profile["nameJa"])} / {esc(profile["nameEn"])}">
  <meta property="og:title" content="{esc(site["title"])}">
  <meta property="og:description" content="{esc(site["description"])}">
  <meta property="og:url" content="{esc(site_url)}">
  <meta property="og:image" content="{esc(og_url)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(profile["nameJa"])}の研究者個人サイト">
  <meta property="profile:first_name" content="Kaede">
  <meta property="profile:last_name" content="Noto">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(site["title"])}">
  <meta name="twitter:description" content="{esc(site["description"])}">
  <meta name="twitter:image" content="{esc(og_url)}">

  <script type="application/ld+json">
{json_ld}
  </script>
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">本文へ移動</a>

  <header class="site-header" id="top">
    <div class="container header-inner">
      <a class="brand" href="#top" aria-label="ページ上部へ戻る">
        <span>{esc(profile["nameJa"])}</span>
        <small>{esc(profile["nameEn"])}</small>
      </a>
      <nav class="nav desktop-nav" aria-label="主要メニュー">
        <a href="#about">研究概要</a>
        <a href="#research">研究テーマ</a>
        <a href="#outputs">主要業績</a>
        <a href="#teaching">教育</a>
        <a href="#links">リンク</a>
      </nav>
      <div class="header-actions">
        <button class="icon-button" type="button" data-theme-toggle aria-label="ダークモードに切り替える" title="表示テーマを切り替える">◐</button>
        <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く">☰</button>
      </div>
    </div>
    <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">
      <a href="#about">研究概要</a>
      <a href="#research">研究テーマ</a>
      <a href="#outputs">主要業績</a>
      <a href="#teaching">教育</a>
      <a href="#links">リンク</a>
    </nav>
  </header>

  <main id="main">
    <section class="hero" aria-labelledby="page-title">
      <div class="container hero-grid">
        <div>
          <h1 id="page-title">{esc(profile["nameJa"])}</h1>
          <p class="hero-name-en" lang="en">{esc(profile["nameEn"])}</p>
          <p class="hero-affiliation">{esc(profile["affiliation"])}　{esc(profile["position"])}</p>
          <p class="hero-summary">{esc(profile["summary"])}</p>
          {render_tags(profile["keywords"], "keyword-list")}
        </div>
        {profile_image_html}
      </div>
    </section>

    <section class="section section--alt" id="about" aria-labelledby="about-title">
      <div class="container two-column">
        <div class="section-heading">
          <p class="section-kicker">About</p>
          <h2 id="about-title">{esc(about["heading"])}</h2>
        </div>
        <div class="prose">
          {about_html}
          <dl class="profile-facts">{fact_html}</dl>
        </div>
      </div>
    </section>

    <section class="section" id="research" aria-labelledby="research-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-kicker">Research</p>
          <h2 id="research-title">{esc(research["heading"])}</h2>
          <p class="section-intro">{esc(research["intro"])}</p>
        </div>
        <div class="card-grid">{render_research(research["areas"])}</div>
      </div>
    </section>

    <section class="section section--alt" id="projects" aria-labelledby="projects-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-kicker">Projects</p>
          <h2 id="projects-title">{esc(projects["heading"])}</h2>
        </div>
        <div class="card-grid">{render_projects(projects["items"])}</div>
      </div>
    </section>

    <section class="section" id="outputs" aria-labelledby="outputs-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-kicker">Selected Works</p>
          <h2 id="outputs-title">{esc(outputs["heading"])}</h2>
          <p class="section-intro">{esc(outputs["intro"])}</p>
        </div>
        <div class="output-list">{render_outputs(outputs["items"])}</div>
        {external_link(outputs["allWorksUrl"], 'Researchmapで業績一覧を見る ↗', 'more-link')}
      </div>
    </section>

    <section class="section section--alt" id="teaching" aria-labelledby="teaching-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-kicker">Teaching</p>
          <h2 id="teaching-title">{esc(teaching["heading"])}</h2>
        </div>
        <div class="card-grid">{render_teaching(teaching["items"])}</div>
      </div>
    </section>

    <section class="section" id="profile" aria-labelledby="profile-title">
      <div class="container two-column">
        <div class="section-heading">
          <p class="section-kicker">Profile</p>
          <h2 id="profile-title">略歴</h2>
        </div>
        <div class="history">{render_history(profile["history"])}</div>
      </div>
    </section>

    <section class="section section--alt" id="links" aria-labelledby="links-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-kicker">Links</p>
          <h2 id="links-title">{esc(links["heading"])}</h2>
          <p class="section-intro">{esc(links["text"])}</p>
        </div>
        <div class="link-grid">{render_links(links["items"])}</div>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>© <span data-current-year></span> {esc(profile["nameEn"])}</p>
      <a href="#top">ページ上部へ戻る</a>
    </div>
  </footer>
</body>
</html>
'''


def build_404(data: dict) -> str:
    site = data["site"]
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>ページが見つかりません</title><link rel="stylesheet" href="styles.css"></head>
<body><main class="section"><div class="container"><h1>ページが見つかりません</h1><p>URLをご確認ください。</p><p><a href="{esc(site["url"])}">トップページへ戻る</a></p></div></main></body></html>'''


def main() -> None:
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    (DIST / "index.html").write_text(build_html(data), encoding="utf-8")
    (DIST / "404.html").write_text(build_404(data), encoding="utf-8")
    shutil.copy2(ROOT / "styles.css", DIST / "styles.css")
    shutil.copy2(ROOT / "script.js", DIST / "script.js")
    shutil.copy2(ROOT / ".nojekyll", DIST / ".nojekyll")
    shutil.copytree(ROOT / "assets", DIST / "assets")

    site_url = safe_url(data["site"]["url"])
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{esc(site_url)}</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
'''
    robots = f'''User-agent: *
Allow: /

Sitemap: {urljoin(site_url, "sitemap.xml")}
'''
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"Built {DIST / 'index.html'}")


if __name__ == "__main__":
    main()
