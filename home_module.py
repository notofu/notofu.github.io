from __future__ import annotations

import json
from datetime import date
from urllib.parse import urljoin

from site_common import esc, favicon_links, header, href, local_url, og_meta, shorten



def _icon(name: str, utility: bool = False) -> str:
    cls = "home-utility-icon" if utility else "home-section-icon"
    common = f'class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"'
    icons = {
        "research": '<rect x="4" y="5" width="7" height="6" rx="1"/><rect x="13" y="4" width="7" height="6" rx="1"/><rect x="8" y="14" width="8" height="6" rx="1"/><path d="M10 11l2 3M15 10l-2 4"/>',
        "news": '<rect x="5" y="6" width="13" height="13" rx="1.5"/><path d="M8 9h7M8 12h7M8 15h5"/><path d="M18 8h2v9a2 2 0 0 1-2 2"/>',
        "publications": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 12h6M9 15h6M9 18h4"/>',
        "teaching": '<path d="M4 5.5c3-1 5-.7 8 1.2 3-1.9 5-2.2 8-1.2v13c-3-1-5-.7-8 1.2-3-1.9-5-2.2-8-1.2z"/><path d="M12 6.7v13"/>',
        "blog": '<path d="M6 4h12v16H6z"/><path d="M9 8h6M9 11h6M9 14h4"/><path d="M16.5 4.5l3 3-6.8 6.8-3.2.7.7-3.2z"/>',
        "contact": '<path d="M4 6h16v12H4z"/><path d="M4.8 7l7.2 6 7.2-6"/>',
    }
    body = icons.get(name, icons["publications"])
    return f'<svg {common} fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'

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
            f'<img src="{esc(image)}" alt="{esc(item.get("imageAlt", ""))}" width="96" height="64" loading="lazy" decoding="async">'
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
        new_badge = '<span class="news-new">NEW</span>' if item.get("isNew") else ""
        rows.append(
            '<article class="home-news-item">'
            f'<div class="home-news-date"><time datetime="{esc(item.get("date", ""))}">{esc(display_date)}</time>{new_badge}</div>'
            f'<p>{title}</p>'
            '</article>'
        )
    return "".join(rows) or '<p class="home-empty">最新情報は準備中です。</p>'


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
    links = data.get("links", {}).get("items", [])

    profile_src = p.get("_optimizedImage") or p.get("image")
    profile_image = (
        f'<img class="home-profile-photo" src="{esc(profile_src)}" alt="{esc(p.get("imageAlt", p["nameJa"]))}" width="82" height="82" loading="eager" decoding="async">'
        if profile_src else '<span class="home-profile-photo home-profile-photo--empty" aria-hidden="true"></span>'
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
    desc = site["description"]

    return f'''<!doctype html><html lang="{esc(site.get("language", "ja"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site["title"])}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(site["url"])}">{favicon_links()}
{og_meta(site, site["title"], desc, site["url"])}<link rel="alternate" type="application/rss+xml" title="noto Lab Feed" href="feed.xml"><link rel="stylesheet" href="styles.css?v=20260808i"><script src="script.js?v=20260808i" defer></script><script type="application/ld+json">{_json_ld(data)}</script></head><body class="home-page">
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="home")}<main id="main">

<section class="home-intro"><div class="container">
  <div class="home-intro-grid">
    <div class="home-intro-copy"><p>{esc(p.get("summary", ""))}</p></div>
    <aside class="home-profile-brief" id="profile" aria-label="Profile">
      <button class="home-profile-photo-button" type="button" data-profile-toggle aria-expanded="false" aria-controls="home-profile-details" aria-label="プロフィール詳細と経歴を表示">
        {profile_image}<span class="home-profile-photo-mark" aria-hidden="true" data-profile-toggle-mark>＋</span>
      </button>
      <div class="home-profile-brief-copy">
        <p class="home-profile-label">Profile</p>
        <h1>{esc(p["nameJa"])} <span>{esc(p["nameEn"])}</span></h1>
        <p>{esc(p["affiliation"])}　{esc(p["position"])}</p>
        <div class="home-profile-links">{external_links}</div>
      </div>
    </aside>
  </div>
  <div class="home-profile-details" id="home-profile-details" data-profile-details hidden>
    <section><h2>Profile Details</h2><dl class="fact-list">{fact_html}</dl></section>
    <section><h2>Career</h2><div class="home-profile-career">{_history(p.get("history", []))}</div></section>
  </div>
</div></section>

<section class="home-dashboard" aria-label="Research Themes, News, Publications"><div class="container home-dashboard-grid">
  <section class="home-panel home-panel--research" id="research"><div class="home-panel-head"><a class="home-panel-title home-panel-title-link" href="research/index.html">{_icon("research")}<h2>Research Themes</h2></a><a href="research/index.html">View all</a></div><div class="home-research-list">{_research_rows(research_items, 3)}</div></section>
  <section class="home-panel home-panel--news" id="news"><div class="home-panel-head"><a class="home-panel-title home-panel-title-link" href="news/index.html">{_icon("news")}<h2>News</h2></a><a href="news/index.html">View all</a></div><div class="home-news-list">{_news_rows(news_items, 5)}</div></section>
  <section class="home-panel home-panel--works" id="works"><div class="home-panel-head"><a class="home-panel-title home-panel-title-link" href="works.html">{_icon("publications")}<h2>Publications</h2></a><a href="works.html">View all</a></div><div class="home-work-list">{_selected_works(all_works, 3)}</div></section>
</div></section>

<nav class="home-utility-nav" aria-label="その他のページ"><div class="container home-utility-grid">
  <a href="teaching.html">{_icon("teaching", True)}<span>Teaching</span><span aria-hidden="true">→</span></a>
  <a href="research/index.html#blog">{_icon("blog", True)}<span>Blog</span><span aria-hidden="true">→</span></a>
  <a href="contact.html">{_icon("contact", True)}<span>Contact</span><span aria-hidden="true">→</span></a>
</div></nav>

</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p></div></footer></body></html>'''

def build_contact_page(data: dict) -> str:
    site, p = data["site"], data["profile"]
    contact = dict(DEFAULT_CONTACT)
    contact.update(data.get("contact") or {})
    canonical = urljoin(site["url"], "contact.html")
    desc = f'{p["nameJa"]}へのお問い合わせ・所在地。'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contact | noto Lab</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(canonical)}">{favicon_links()}
{og_meta(site, "Contact | noto Lab", desc, canonical)}<link rel="stylesheet" href="styles.css?v=20260808i"><script src="script.js?v=20260808i" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="contact")}<main id="main">
<section class="works-hero contact-page-hero"><div class="container"><a class="back-link" href="index.html">← トップページへ戻る</a><p class="eyebrow">noto Lab</p><h1>Contact</h1><p>研究、共同研究、教育活動などに関するご連絡はこちらからお願いします。</p></div></section>
<section class="contact-section contact-page-section"><div class="container contact-grid"><div class="contact-info"><h2>お問い合わせ・所在地</h2><dl class="contact-details"><div><dt>Email</dt><dd>{esc(contact.get("displayEmail", ""))}</dd></div><div><dt>Affiliation</dt><dd>{esc(contact.get("institution", ""))}</dd></div><div><dt>Location</dt><dd>{esc(contact.get("postalCode", ""))}<br>{esc(contact.get("address", ""))}<br><a href="{esc(contact.get("mapsUrl", ""))}" target="_blank" rel="noopener noreferrer">Google Mapsで見る ↗</a></dd></div></dl></div>
<form class="contact-form" data-contact-form data-email-user="{esc(contact.get("emailUser", ""))}" data-email-domain="{esc(contact.get("emailDomain", ""))}"><label>お名前<input name="name" autocomplete="name" required></label><label>返信先メールアドレス<input name="email" type="email" autocomplete="email" required></label><label>件名<input name="subject" required></label><label>本文<textarea name="message" rows="7" required></textarea></label><div class="contact-form-actions"><button type="submit">メールを作成 →</button><p>送信ボタンを押すと、端末のメールアプリが開きます。</p></div></form></div></section>
</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="index.html">トップページへ戻る ←</a></div></footer></body></html>'''
