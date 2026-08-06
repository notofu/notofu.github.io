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
            '<article class="timeline-item">'
            f'<div class="timeline-period">{esc(item["period"])}</div>'
            '<div class="timeline-body">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["detail"])}</p>'
            '</div></article>'
        )
    return "".join(rows)


def render_research(items: list[dict]) -> str:
    default_images = [
        ("assets/research-melody.png", "旋律の音高推移と構造区間を表した抽象図"),
        ("assets/research-performance.png", "演奏データと個人差を表した抽象図"),
        ("assets/research-gaze.png", "楽譜と鍵盤への視線移動を表した抽象図"),
        ("assets/research-ensemble.png", "複数演奏者の同期と位相関係を表した抽象図"),
    ]
    cards = []
    for index, item in enumerate(items, 1):
        default_image, default_alt = default_images[(index - 1) % len(default_images)]
        image = item.get("image") or default_image
        image_alt = item.get("imageAlt") or default_alt
        image_html = ""
        if image:
            image_html = (
                '<div class="research-image">'
                f'<img src="{esc(image)}" alt="{esc(image_alt)}" width="720" height="420" loading="lazy">'
                '</div>'
            )
        cards.append(
            '<article class="research-card">'
            f'{image_html}'
            '<div class="research-card-body">'
            f'<div class="research-index">0{index}</div>'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{render_tags(item.get("tags", []))}'
            '</div></article>'
        )
    return "".join(cards)


def render_projects(items: list[dict]) -> str:
    rows = []
    for item in items:
        link = external_link(item.get("url", ""), "詳細を見る", "text-link")
        rows.append(
            '<article class="project-row">'
            f'<div class="project-period">{esc(item["period"])}</div>'
            '<div class="project-content">'
            f'<h3>{esc(item["title"])}</h3>'
            f'<p>{esc(item["description"])}</p>'
            f'{link}'
            '</div></article>'
        )
    return "".join(rows)


def render_outputs(items: list[dict]) -> str:
    rows = []
    for item in items:
        title = esc(item["title"])
        if item.get("url"):
            title = external_link(item["url"], title)
        meta_parts = [part for part in (item.get("venue", ""), item.get("authors", "")) if part]
        meta = " / ".join(esc(part) for part in meta_parts)
        rows.append(
            '<article class="output-row">'
            '<div class="output-meta">'
            f'<span class="output-year">{esc(item["year"])}</span>'
            f'<span class="output-type">{esc(item["type"])}</span>'
            '</div>'
            '<div class="output-content">'
            f'<h3>{title}</h3>'
            f'<p>{meta}</p>'
            '</div></article>'
        )
    return "".join(rows)


def render_teaching(items: list[dict]) -> str:
    cards = []
    for item in items:
        cards.append(
            '<article class="teaching-card">'
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
            '<span class="link-card-copy">'
            f'<strong>{esc(item["label"])}</strong>'
            f'<small>{esc(item["description"])}</small>'
            '</span>'
            '<span class="link-arrow" aria-hidden="true">↗</span>'
            '</a>'
        )
    return "".join(cards)


def build_json_ld(data: dict) -> str:
    site = data["site"]
    profile = data["profile"]
    same_as = [item["url"] for item in data["links"]["items"] if item.get("sameAs", False)]
    image_url = urljoin(site["url"], profile["image"]) if profile.get("image") else ""

    person_id = urljoin(site["url"], "#person")
    page_id = urljoin(site["url"], "#profile-page")
    website_id = urljoin(site["url"], "#website")

    person = {
        "@type": "Person",
        "@id": person_id,
        "name": profile["nameJa"],
        "alternateName": profile["nameEn"],
        "url": site["url"],
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
    }
    if image_url:
        person["image"] = image_url

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
            person,
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
            '<div class="profile-photo-wrap">'
            f'<img class="profile-photo" src="{esc(profile_image)}" '
            f'alt="{esc(profile["imageAlt"])}" width="76" height="76" fetchpriority="high">'
            '</div>'
        )

    facts = [
        ("所属", profile["affiliation"]),
        ("職位", profile["position"]),
        ("学位", profile["degree"]),
        ("拠点", profile["location"]),
    ]
    fact_html = "".join(
        f'<div class="fact-row"><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>'
        for label, value in facts
    )
    about_html = "".join(f"<p>{esc(p)}</p>" for p in about["paragraphs"])
    json_ld = build_json_ld(data)
    verification = site.get("googleSiteVerification", "").strip()
    verification_meta = (
        f'<meta name="google-site-verification" content="{esc(verification)}">'
        if verification else ""
    )

    return f'''<!doctype html>
<html lang="{esc(site["language"])}">
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
      <nav class="desktop-nav" aria-label="主要メニュー">
        <a href="#about">研究概要</a>
        <a href="#research">研究テーマ</a>
        <a href="#outputs">主要業績</a>
        <a href="#teaching">教育</a>
        <a href="#profile">略歴</a>
      </nav>
      <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く">
        <span></span><span></span><span></span>
      </button>
    </div>
    <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">
      <a href="#about">研究概要</a>
      <a href="#research">研究テーマ</a>
      <a href="#outputs">主要業績</a>
      <a href="#teaching">教育</a>
      <a href="#profile">略歴</a>
      <a href="#links">外部リンク</a>
    </nav>
  </header>

  <main id="main">
    <section class="hero" aria-labelledby="page-title">
      <div class="container hero-shell">
        <div class="identity-row">
          {profile_image_html}
          <div class="identity-copy">
            <p class="identity-name"><strong>{esc(profile["nameJa"])}</strong><span lang="en">{esc(profile["nameEn"])}</span></p>
            <p class="identity-affiliation">{esc(profile["affiliation"])}<br><span>{esc(profile["position"])}・{esc(profile["degree"])}</span></p>
          </div>
        </div>

        <div class="hero-main">
          <div class="hero-copy">
            <p class="eyebrow">RESEARCHER PROFILE</p>
            <h1 id="page-title">研究・教育活動</h1>
            <p class="hero-summary">{esc(profile["summary"])}</p>
            {render_tags(profile["keywords"], "keyword-list")}
            <div class="hero-actions">
              <a class="primary-button" href="#research">研究テーマを見る</a>
              {external_link(outputs["allWorksUrl"], 'Researchmapで業績を見る', 'secondary-button')}
            </div>
          </div>

          <nav class="hero-shortcuts" aria-label="主要コンテンツへのリンク">
            <a href="#research"><span>RESEARCH</span><strong>研究テーマ</strong><small>{len(research["areas"])}件の研究領域</small></a>
            <a href="#outputs"><span>OUTPUTS</span><strong>主要業績</strong><small>論文・国際会議発表</small></a>
            <a href="#profile"><span>PROFILE</span><strong>略歴</strong><small>所属・学位・経歴</small></a>
          </nav>
        </div>
      </div>
    </section>

    <section class="section section-soft" id="about" aria-labelledby="about-title">
      <div class="container split-layout">
        <div class="section-heading sticky-heading">
          <p class="section-label">ABOUT</p>
          <h2 id="about-title">{esc(about["heading"])}</h2>
        </div>
        <div class="prose">{about_html}</div>
      </div>
    </section>

    <section class="section" id="research" aria-labelledby="research-title">
      <div class="container">
        <div class="section-heading section-heading-wide">
          <div>
            <p class="section-label">RESEARCH</p>
            <h2 id="research-title">{esc(research["heading"])}</h2>
          </div>
          <p class="section-intro">{esc(research["intro"])}</p>
        </div>
        <div class="research-grid">{render_research(research["areas"])}</div>
      </div>
    </section>

    <section class="section section-soft" id="projects" aria-labelledby="projects-title">
      <div class="container split-layout">
        <div class="section-heading sticky-heading">
          <p class="section-label">PROJECTS</p>
          <h2 id="projects-title">{esc(projects["heading"])}</h2>
        </div>
        <div class="project-list">{render_projects(projects["items"])}</div>
      </div>
    </section>

    <section class="section" id="outputs" aria-labelledby="outputs-title">
      <div class="container">
        <div class="section-heading section-heading-wide">
          <div>
            <p class="section-label">SELECTED WORKS</p>
            <h2 id="outputs-title">{esc(outputs["heading"])}</h2>
          </div>
          <div>
            <p class="section-intro">{esc(outputs["intro"])}</p>
            {external_link(outputs["allWorksUrl"], 'Researchmapで全件を見る', 'text-link')}
          </div>
        </div>
        <div class="output-list">{render_outputs(outputs["items"])}</div>
      </div>
    </section>

    <section class="section section-soft" id="teaching" aria-labelledby="teaching-title">
      <div class="container">
        <div class="section-heading">
          <p class="section-label">TEACHING</p>
          <h2 id="teaching-title">{esc(teaching["heading"])}</h2>
        </div>
        <div class="teaching-grid">{render_teaching(teaching["items"])}</div>
      </div>
    </section>

    <section class="section" id="profile" aria-labelledby="profile-title">
      <div class="container split-layout">
        <div class="section-heading sticky-heading">
          <p class="section-label">PROFILE</p>
          <h2 id="profile-title">略歴</h2>
        </div>
        <div class="timeline">{render_history(profile["history"])}</div>
      </div>
    </section>

    <section class="section section-contact" id="links" aria-labelledby="links-title">
      <div class="container link-section-layout">
        <div class="section-heading">
          <p class="section-label">LINKS</p>
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
<body><main class="error-page"><div><p class="section-label">404</p><h1>ページが見つかりません</h1><p>URLをご確認ください。</p><a class="primary-button" href="{esc(site["url"])}">トップページへ戻る</a></div></main></body></html>'''


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
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{esc(site_url)}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n'
        '</urlset>\n'
    )
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    robots = f"User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, 'sitemap.xml')}\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"Built site at: {DIST}")


if __name__ == "__main__":
    main()
