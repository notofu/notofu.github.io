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


def render_keyword_line(items: list[str]) -> str:
    if not items:
        return ""
    return '<p class="keyword-line">' + ''.join(f'<span>{esc(x)}</span>' for x in items) + '</p>'


def render_research(items: list[dict]) -> str:
    rows = []
    for i, item in enumerate(items, 1):
        image = item.get("image", "").strip()
        image_html = ""
        item_cls = "research-item"
        if image:
            alt = item.get("imageAlt") or f'{item["title"]}の研究イメージ'
            image_html = f'<img class="research-image" src="{esc(image)}" alt="{esc(alt)}" width="440" height="264" loading="lazy">'
            item_cls += " has-image"
        tags = item.get("tags", [])
        tag_html = ""
        if tags:
            tag_html = '<ul class="research-tags">' + ''.join(f'<li>{esc(t)}</li>' for t in tags) + '</ul>'
        rows.append(
            f'<article class="{item_cls}">'
            f'<div class="research-index">{i:02d}</div>'
            '<div class="research-body">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{tag_html}'
            '</div>'
            f'{image_html}'
            '</article>'
        )
    return ''.join(rows)


def render_projects(items: list[dict]) -> str:
    rows = []
    for item in items:
        rows.append(
            '<article class="plain-row">'
            f'<div class="plain-meta">{esc(item["period"])}</div>'
            '<div class="plain-main">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{href(item.get("url", ""), "詳細を見る ↗", "text-link")}'
            '</div></article>'
        )
    return ''.join(rows)


def render_outputs(items: list[dict]) -> str:
    rows = []
    for item in items:
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
    return ''.join(rows)


def render_teaching(items: list[dict]) -> str:
    return ''.join(
        '<article class="teaching-item">'
        f'<h3>{esc(item["title"])}</h3>'
        f'<p>{esc(item["description"])}</p>'
        '</article>'
        for item in items
    )


def render_history(items: list[dict]) -> str:
    return ''.join(
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
    return ''.join(rows)


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
        ]
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def build_html(data: dict) -> str:
    site, p = data["site"], data["profile"]
    about, research = data["about"], data["research"]
    projects, outputs = data["projects"], data["outputs"]
    teaching, links = data["teaching"], data["links"]
    site_url = site["url"]
    og_url = urljoin(site_url, site["ogImage"])
    profile_image = ""
    if p.get("image"):
        profile_image = f'<img class="profile-photo" src="{esc(p["image"])}" alt="{esc(p["imageAlt"])}" width="72" height="72" fetchpriority="high">'
    facts = [("所属", p["affiliation"]), ("職位", p["position"]), ("学位", p["degree"]), ("拠点", p["location"])]
    facts_html = ''.join(f'<div class="fact-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
    about_html = ''.join(f'<p>{esc(x)}</p>' for x in about["paragraphs"])
    verification = site.get("googleSiteVerification", "").strip()
    verify_meta = f'<meta name="google-site-verification" content="{esc(verification)}">' if verification else ""

    return f'''<!doctype html>
<html lang="{esc(site["language"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(site["title"])}</title>
  <meta name="description" content="{esc(site["description"])}">
  <meta name="author" content="{esc(p["nameJa"])}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
  <meta name="theme-color" content="{esc(site["themeColor"])}">
  {verify_meta}
  <link rel="canonical" href="{esc(site_url)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <meta property="og:type" content="profile">
  <meta property="og:locale" content="ja_JP">
  <meta property="og:title" content="{esc(site["title"])}">
  <meta property="og:description" content="{esc(site["description"])}">
  <meta property="og:url" content="{esc(site_url)}">
  <meta property="og:image" content="{esc(og_url)}">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{build_json_ld(data)}</script>
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">本文へ移動</a>
<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="#top">{esc(p["nameJa"])} <small>{esc(p["nameEn"])}</small></a>
    <nav class="desktop-nav" aria-label="主要メニュー">
      <a href="#research">Research</a>
      <a href="#outputs">Publications</a>
      <a href="#teaching">Teaching</a>
      <a href="#profile">Profile</a>
      <a href="#links">Links</a>
    </nav>
    <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く"><span></span><span></span><span></span></button>
  </div>
  <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">
    <a href="#research">Research</a><a href="#outputs">Publications</a><a href="#teaching">Teaching</a><a href="#profile">Profile</a><a href="#links">Links</a>
  </nav>
</header>

<main id="main">
  <section class="hero">
    <div class="container">
      <div class="profile-intro">
        {profile_image}
        <div class="profile-copy">
          <h1>{esc(p["nameJa"])}</h1>
          <p class="profile-name-en">{esc(p["nameEn"])}</p>
          <p class="profile-role">{esc(p["position"])} / {esc(p["affiliation"])}</p>
        </div>
      </div>
      <p class="hero-summary">{esc(p["summary"])}</p>
      {render_keyword_line(p["keywords"])}
      <div class="hero-links">
        <a href="#research">研究テーマ ↓</a>
        {href(outputs["allWorksUrl"], "研究業績 ↗")}
        {href(next((x["url"] for x in links["items"] if x["label"].lower() == "researchmap"), ""), "Researchmap ↗")}
      </div>
    </div>
  </section>

  <section class="section" id="about" aria-labelledby="about-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="about-title">{esc(about["heading"])}</h2><p class="section-label">ABOUT</p></div><p class="section-intro">音楽演奏における知覚・予測・学習・相互作用を、データ分析と計算モデルから検討しています。</p></div>
      <div class="prose">{about_html}</div>
    </div>
  </section>

  <section class="section" id="research" aria-labelledby="research-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="research-title">{esc(research["heading"])}</h2><p class="section-label">RESEARCH</p></div><p class="section-intro">{esc(research["intro"])}</p></div>
      <div class="research-list">{render_research(research["areas"])}</div>
    </div>
  </section>

  <section class="section" id="projects" aria-labelledby="projects-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="projects-title">{esc(projects["heading"])}</h2><p class="section-label">PROJECTS</p></div><p class="section-intro">現在進行中・継続中の研究プロジェクトです。</p></div>
      <div class="plain-list">{render_projects(projects["items"])}</div>
    </div>
  </section>

  <section class="section" id="outputs" aria-labelledby="outputs-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="outputs-title">{esc(outputs["heading"])}</h2><p class="section-label">SELECTED PUBLICATIONS</p></div><p class="section-intro">{esc(outputs["intro"])}</p></div>
      <div class="output-list">{render_outputs(outputs["items"])}</div>
      <p class="section-more">{href(outputs["allWorksUrl"], "すべての研究業績を見る →")}</p>
    </div>
  </section>

  <section class="section" id="teaching" aria-labelledby="teaching-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="teaching-title">{esc(teaching["heading"])}</h2><p class="section-label">TEACHING</p></div><p class="section-intro">担当する主な科目・教育内容です。</p></div>
      <div class="teaching-list">{render_teaching(teaching["items"])}</div>
    </div>
  </section>

  <section class="section" id="profile" aria-labelledby="profile-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="profile-title">プロフィール</h2><p class="section-label">PROFILE</p></div><p class="section-intro">所属・学位・略歴。</p></div>
      <div class="profile-layout"><dl class="fact-list">{facts_html}</dl><div class="timeline">{render_history(p["history"])}</div></div>
    </div>
  </section>

  <section class="section" id="links" aria-labelledby="links-title">
    <div class="container">
      <div class="section-heading"><div><h2 id="links-title">{esc(links["heading"])}</h2><p class="section-label">LINKS</p></div><p class="section-intro">{esc(links["text"])}</p></div>
      <div class="link-list">{render_links(links["items"])}</div>
    </div>
  </section>
</main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer>
</body></html>'''


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
    site_url = data["site"]["url"]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + f'  <url><loc>{esc(site_url)}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n' + f'  <url><loc>{esc(urljoin(site_url, "works.html"))}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n</urlset>\n'
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, "sitemap.xml")}\n', encoding="utf-8")
    print(f"Built site at: {DIST}")


if __name__ == "__main__":
    main()
