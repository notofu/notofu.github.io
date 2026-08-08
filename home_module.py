from __future__ import annotations

import json
from datetime import date
from urllib.parse import urljoin

from site_common import esc, favicon_links, header, href, local_url, og_meta, shorten

DEFAULT_CONTACT = {
    "emailUser": "notokaede",
    "emailDomain": "gmail.com",
    "displayEmail": "notokaede [at] gmail.com",
    "institution": "函館工業高等専門学校 生産システム工学科 情報コース",
    "postalCode": "〒042-8501",
    "address": "北海道函館市戸倉町14-1",
    "mapsUrl": "https://www.google.com/maps/search/?api=1&query=%E5%87%BD%E9%A4%A8%E5%B7%A5%E6%A5%AD%E9%AB%98%E7%AD%89%E5%B0%82%E9%96%80%E5%AD%A6%E6%A0%A1",
}


def _json_ld(data: dict) -> str:
    site, p = data["site"], data["profile"]
    same_as = [x["url"] for x in data.get("links", {}).get("items", []) if x.get("sameAs")]
    person = {
        "@type": "Person",
        "@id": urljoin(site["url"], "#person"),
        "name": p["nameJa"],
        "alternateName": p["nameEn"],
        "url": site["url"],
        "description": p["summary"],
        "jobTitle": p["position"],
        "affiliation": {
            "@type": "CollegeOrUniversity",
            "name": p["affiliationEn"],
            "url": "https://www.hakodate-ct.ac.jp/",
        },
        "knowsAbout": p.get("keywords", []),
        "sameAs": same_as,
        "workLocation": {
            "@type": "Place",
            "name": "函館工業高等専門学校",
            "address": {
                "@type": "PostalAddress",
                "postalCode": "042-8501",
                "addressRegion": "北海道",
                "addressLocality": "函館市",
                "streetAddress": "戸倉町14-1",
                "addressCountry": "JP",
            },
        },
    }
    if p.get("image"):
        person["image"] = urljoin(site["url"], p["image"])
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "url": site["url"],
                "name": "noto Lab",
                "alternateName": f'{p["nameJa"]} / {p["nameEn"]}',
                "inLanguage": site.get("language", "ja"),
            },
            {
                "@type": "ProfilePage",
                "url": site["url"],
                "name": site["title"],
                "description": site["description"],
                "dateModified": date.today().isoformat(),
                "mainEntity": person,
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def _work_kind(type_text: object) -> tuple[str, str]:
    t = str(type_text or "")
    low = t.lower()
    if t == "paper" or "査読" in t or ("論文" in t and "国際" not in t):
        return "journal", "論文"
    if "conference" in low or "国際会議" in t:
        return "conference", "国際会議"
    if t == "presentation" or "発表" in t or "研究会" in t:
        return "presentation", "発表"
    if t == "misc" or "misc" in low:
        return "report", "MISC"
    return "other", t or "業績"


def _selected_works(records: list[dict], limit: int = 3) -> str:
    rows = []
    for item in records[:limit]:
        kind, label = _work_kind(item.get("type", ""))
        title = esc(item.get("title", ""))
        if item.get("url"):
            title = f'<a href="{esc(item["url"])}" target="_blank" rel="noopener noreferrer">{title}</a>'
        rows.append(
            f'<article class="home-work-item" data-kind="{esc(kind)}">'
            f'<span class="home-type-badge">{esc(label)}</span>'
            '<div class="home-work-copy">'
            f'<h3>{title}</h3>'
            f'<p>{esc(item.get("venue", ""))}</p>'
            '</div>'
            f'<time>{esc(item.get("year", ""))}</time>'
            '<span class="home-row-arrow" aria-hidden="true">›</span>'
            '</article>'
        )
    return "".join(rows) or '<p class="home-empty">公開中の研究業績はありません。</p>'


def _research_rows(items: list[dict], limit: int = 3) -> str:
    rows = []
    for item in items[:limit]:
        url = local_url(item.get("url", ""))
        image = item.get("thumbnailSmall") or item.get("thumbnail") or item.get("image") or "assets/favicon.svg"
        image = local_url(image)
        fallback = " is-fallback" if item.get("_imageFallback") else ""
        rows.append(
            '<article class="home-research-item">'
            f'<a class="home-research-thumb{fallback}" href="{esc(url)}" aria-label="{esc(item.get("title", ""))}の詳細を見る">'
            f'<img src="{esc(image)}" alt="{esc(item.get("imageAlt", ""))}" width="96" height="72" loading="lazy" decoding="async">'
            '</a>'
            '<div class="home-research-copy">'
            f'<h3><a href="{esc(url)}">{esc(item.get("title", ""))}</a></h3>'
            f'<p>{esc(shorten(item.get("summary", ""), 54))}</p>'
            '</div>'
            '</article>'
        )
    return "".join(rows) or '<p class="home-empty">公開中の研究テーマはありません。</p>'


def _news_rows(items: list[dict], limit: int = 5) -> str:
    rows = []
    for item in items[:limit]:
        url = local_url(item.get("url", ""))
        title = esc(item.get("title", ""))
        if url and url != "#":
            title = f'<a href="{esc(url)}">{title}</a>'
        display_date = str(item.get("date", "")).replace("-", ".")
        new_badge = '<span class="news-new">NEW!</span>' if item.get("isNew") else ""
        rows.append(
            '<article class="home-news-item">'
            f'<div class="home-news-date"><time datetime="{esc(item.get("date", ""))}">{esc(display_date)}</time>{new_badge}</div>'
            f'<p>{title}</p>'
            '</article>'
        )
    return "".join(rows) or '<p class="home-empty">最新情報は準備中です。</p>'


def _teaching_preview(items: list[dict], limit: int = 3) -> str:
    rows = []
    for item in items[:limit]:
        rows.append(
            '<li>'
            f'<strong>{esc(item.get("title", ""))}</strong>'
            f'<span>{esc(shorten(item.get("description", ""), 42))}</span>'
            '</li>'
        )
    return "".join(rows) or '<li><span>公開中の授業情報はありません。</span></li>'


def _blog_preview(items: list[dict], limit: int = 3) -> str:
    rows = []
    for item in items[:limit]:
        url = local_url(item.get("url", ""))
        rows.append(
            '<li>'
            f'<time>{esc(str(item.get("date", "")).replace("-", "."))}</time>'
            f'<a href="{esc(url)}">{esc(item.get("title", ""))}</a>'
            '</li>'
        )
    return "".join(rows) or '<li><span>公開中のBlog記事はありません。</span></li>'


def _hero_visual(items: list[dict]) -> str:
    # Heroでは複数画像を組み合わせず、既存の研究画像を1枚だけ静かに見せる。
    if not items:
        return '<div class="home-hero-placeholder" aria-hidden="true"><img src="assets/favicon.svg" alt=""></div>'
    item = next((x for x in items if not x.get("_imageFallback")), items[0])
    image = item.get("thumbnailLarge") or item.get("thumbnail") or item.get("image") or "assets/favicon.svg"
    image = local_url(image)
    fallback = " is-fallback" if item.get("_imageFallback") else ""
    return (
        f'<figure class="home-hero-single{fallback}">'
        f'<img src="{esc(image)}" alt="{esc(item.get("imageAlt", ""))}" loading="eager" decoding="async">'
        '</figure>'
    )


def _history(items: list[dict]) -> str:
    return "".join(
        '<article class="timeline-item">'
        f'<div class="timeline-period">{esc(x.get("period", ""))}</div>'
        f'<div class="timeline-body"><h3>{esc(x.get("title", ""))}</h3><p>{esc(x.get("detail", ""))}</p></div>'
        '</article>'
        for x in items
    )


def build_home(data: dict, content_items: list[dict], news_items: list[dict], all_works: list[dict], teaching_rows: list[dict]) -> str:
    site, p = data["site"], data["profile"]
    research_items = [x for x in content_items if x["category"] == "research"]
    blog_items = [x for x in content_items if x["category"] == "blog"]
    links = data.get("links", {}).get("items", [])
    contact = dict(DEFAULT_CONTACT)
    contact.update(data.get("contact") or {})

    profile_src = p.get("_optimizedImage") or p.get("image")
    profile_image = (
        f'<img class="profile-photo" src="{esc(profile_src)}" alt="{esc(p.get("imageAlt", p["nameJa"]))}" width="148" height="148" loading="lazy" decoding="async">'
        if profile_src else ""
    )
    external_links = "".join(
        href(
            x.get("url", ""),
            esc("researchmap" if str(x.get("label", "")).lower() == "researchmap" else x.get("label", "")) + " ↗",
        )
        for x in links[:3]
    )
    facts = [
        ("所属", p.get("affiliation", "")),
        ("職位", p.get("position", "")),
        ("学位", p.get("degree", "")),
        ("拠点", p.get("location", "")),
    ]
    fact_html = "".join(f'<div class="fact-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)

    # 既存コンテンツだけを再配置する。新しい素材・説明文は追加しない。
    home_heading = site.get("homeTagline") or "音楽と人の振る舞いを研究する"
    desc = site["description"]

    return f'''<!doctype html><html lang="{esc(site.get("language", "ja"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site["title"])}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(site["url"])}">{favicon_links()}
{og_meta(site, site["title"], desc, site["url"])}<link rel="alternate" type="application/rss+xml" title="noto Lab Feed" href="feed.xml"><link rel="stylesheet" href="styles.css?v=20260808c"><script src="script.js?v=20260808c" defer></script><script type="application/ld+json">{_json_ld(data)}</script></head><body class="home-page">
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="home")}<main id="main">

<section class="home-hero" id="overview"><div class="container home-hero-grid">
  <div class="home-hero-copy"><h1>{esc(home_heading)}</h1><p class="home-hero-summary">{esc(p.get("summary", ""))}</p></div>
  <div class="home-hero-visual">{_hero_visual(research_items)}</div>
</div></section>

<section class="home-dashboard" aria-label="Research Themes, News, Publications"><div class="container home-dashboard-grid">
  <section class="home-panel home-panel--research" id="research"><div class="home-panel-head"><h2>Research Themes</h2><a href="research/index.html">View all →</a></div><div class="home-research-list">{_research_rows(research_items, 3)}</div></section>
  <section class="home-panel home-panel--news" id="news"><div class="home-panel-head"><h2>News</h2><a href="news/index.html">View all →</a></div><div class="home-news-list">{_news_rows(news_items, 5)}</div></section>
  <section class="home-panel home-panel--works" id="works"><div class="home-panel-head"><h2>Publications</h2><a href="works.html">View all →</a></div><div class="home-work-list">{_selected_works(all_works, 3)}</div></section>
</div></section>

<section class="home-quicklinks"><div class="container home-quicklinks-grid">
  <section class="home-quick-card"><div><h2>Teaching</h2><ul class="home-mini-list home-mini-list--compact">{_teaching_preview(teaching_rows, 2)}</ul></div><a class="home-quick-arrow" href="teaching.html" aria-label="Teachingを見る">→</a></section>
  <section class="home-quick-card"><div><h2>Blog</h2><ul class="home-blog-list home-blog-list--compact">{_blog_preview(blog_items, 2)}</ul></div><a class="home-quick-arrow" href="research/index.html#blog" aria-label="Blogを見る">→</a></section>
  <section class="home-quick-card"><div><h2>Contact / Access</h2><p>{esc(contact.get("displayEmail", ""))}</p><p class="home-contact-place">{esc(contact.get("address", ""))}</p></div><a class="home-quick-arrow" href="#contact" aria-label="Contact / Accessを見る">→</a></section>
</div></section>

<section class="profile-section" id="profile"><div class="container profile-identity"><div class="profile-identity-main">{profile_image}<div><p class="eyebrow">Profile</p><h2>{esc(p["nameJa"])} <span>{esc(p["nameEn"])}</span></h2><p class="profile-affiliation">{esc(p["affiliation"])}　{esc(p["position"])}</p><div class="profile-links">{external_links}</div></div></div></div><div class="container profile-section-grid"><div><h3>Profile Details</h3><dl class="fact-list">{fact_html}</dl></div><div><h3>Career</h3><div>{_history(p.get("history", []))}</div></div></div></section>

<section class="contact-section" id="contact"><div class="container contact-grid"><div class="contact-info"><p class="eyebrow">Contact</p><h2>お問い合わせ</h2><p class="contact-lead">研究、共同研究、教育活動などに関するご連絡はこちらからお願いします。</p><dl class="contact-details"><div><dt>Email</dt><dd>{esc(contact.get("displayEmail", ""))}</dd></div><div><dt>Affiliation</dt><dd>{esc(contact.get("institution", ""))}</dd></div><div><dt>Location</dt><dd>{esc(contact.get("postalCode", ""))}<br>{esc(contact.get("address", ""))}<br><a href="{esc(contact.get("mapsUrl", ""))}" target="_blank" rel="noopener noreferrer">Google Mapsで見る ↗</a></dd></div></dl></div>
<form class="contact-form" data-contact-form data-email-user="{esc(contact.get("emailUser", ""))}" data-email-domain="{esc(contact.get("emailDomain", ""))}"><label>お名前<input name="name" autocomplete="name" required></label><label>返信先メールアドレス<input name="email" type="email" autocomplete="email" required></label><label>件名<input name="subject" required></label><label>本文<textarea name="message" rows="7" required></textarea></label><div class="contact-form-actions"><button type="submit">メールを作成 →</button><p>送信ボタンを押すと、端末のメールアプリが開きます。</p></div></form></div></section>
</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''
