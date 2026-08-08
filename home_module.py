from __future__ import annotations

import json
from datetime import date
from urllib.parse import urljoin

from content_module import render_content_cards
from news_module import render_news
from site_common import esc, favicon_links, header, href, og_meta, shorten
from teaching_module import render_teaching_cards

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
        "@type": "Person", "@id": urljoin(site["url"], "#person"), "name": p["nameJa"],
        "alternateName": p["nameEn"], "url": site["url"], "description": p["summary"],
        "jobTitle": p["position"], "affiliation": {"@type": "CollegeOrUniversity", "name": p["affiliationEn"], "url": "https://www.hakodate-ct.ac.jp/"},
        "knowsAbout": p.get("keywords", []), "sameAs": same_as,
        "workLocation": {"@type": "Place", "name": "函館工業高等専門学校", "address": {"@type": "PostalAddress", "postalCode": "042-8501", "addressRegion": "北海道", "addressLocality": "函館市", "streetAddress": "戸倉町14-1", "addressCountry": "JP"}},
    }
    if p.get("image"): person["image"] = urljoin(site["url"], p["image"])
    graph = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "url": site["url"], "name": "noto Lab", "alternateName": f'{p["nameJa"]} / {p["nameEn"]}', "inLanguage": site.get("language", "ja")},
        {"@type": "ProfilePage", "url": site["url"], "name": site["title"], "description": site["description"], "dateModified": date.today().isoformat(), "mainEntity": person},
    ]}
    return json.dumps(graph, ensure_ascii=False, indent=2).replace("</", "<\\/")


def _selected_works(records: list[dict], limit: int = 3) -> str:
    rows = []
    for item in records[:limit]:
        t = str(item.get("type", ""))
        if t == "paper" or "論文" in t: kind, label = "journal", "論文"
        elif t == "presentation" or "発表" in t: kind, label = "presentation", "発表"
        elif t == "misc": kind, label = "report", "MISC"
        else: kind, label = "conference", "国際会議"
        title = esc(item.get("title", ""))
        if item.get("url"):
            title = f'<a href="{esc(item["url"])}" target="_blank" rel="noopener noreferrer">{title}</a>'
        rows.append(
            '<article class="publication-item">'
            f'<span class="pub-badge pub-badge--{kind}">{esc(label)}</span><div class="publication-copy"><h3>{title}</h3><p>{esc(item.get("venue", ""))}</p></div>'
            f'<div class="publication-year">{esc(item.get("year", ""))}</div><div class="publication-arrow" aria-hidden="true">›</div></article>'
        )
    return "".join(rows)


def _history(items: list[dict]) -> str:
    return "".join(
        '<article class="timeline-item">' f'<div class="timeline-period">{esc(x.get("period", ""))}</div>'
        f'<div class="timeline-body"><h3>{esc(x.get("title", ""))}</h3><p>{esc(x.get("detail", ""))}</p></div></article>' for x in items
    )


def build_home(data: dict, content_items: list[dict], news_items: list[dict], all_works: list[dict], teaching_rows: list[dict]) -> str:
    site, p = data["site"], data["profile"]
    research_items = [x for x in content_items if x["category"] == "research"][:6]
    links = data.get("links", {}).get("items", [])
    contact = dict(DEFAULT_CONTACT); contact.update(data.get("contact") or {})
    profile_src = p.get("_optimizedImage") or p.get("image")
    profile_image = f'<img class="profile-photo" src="{esc(profile_src)}" alt="{esc(p.get("imageAlt", p["nameJa"]))}" width="148" height="148" loading="lazy" decoding="async">' if profile_src else ""
    external_links = "".join(href(x.get("url", ""), esc("researchmap" if str(x.get("label", "")).lower() == "researchmap" else x.get("label", "")) + " ↗") for x in links[:3])
    facts = [("所属", p.get("affiliation", "")), ("職位", p.get("position", "")), ("学位", p.get("degree", "")), ("拠点", p.get("location", ""))]
    fact_html = "".join(f'<div class="fact-row"><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
    home_heading = site.get("homeHeading", "Research & Education")
    home_kicker = site.get("homeKicker", "Music Information Processing · Human–Computer Interaction")
    research_cards = render_content_cards(research_items, include_category=False)
    desc = site["description"]
    return f'''<!doctype html><html lang="{esc(site.get("language", "ja"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site["title"])}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(site["url"])}">{favicon_links()}
{og_meta(site, site["title"], desc, site["url"])}<link rel="alternate" type="application/rss+xml" title="noto Lab Feed" href="feed.xml"><link rel="stylesheet" href="styles.css"><script src="script.js" defer></script><script type="application/ld+json">{_json_ld(data)}</script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="home")}<main id="main">
<section class="hero" id="overview"><div class="container hero-grid"><div class="overview-lead"><p class="eyebrow">{esc(home_kicker)}</p><h1>{esc(home_heading)}</h1><p class="overview-summary">{esc(shorten(p["summary"], 76))}</p><div class="overview-actions"><a class="text-link" href="#research">研究テーマを見る ↓</a><a class="text-link" href="works.html">研究業績を見る →</a></div></div>
<section class="news-panel" id="news" aria-labelledby="news-title"><div class="section-mini-head"><h2 id="news-title"><a href="news/index.html">News</a></h2><a href="news/index.html">すべて見る →</a></div><div class="news-list">{render_news(news_items, limit=3)}</div></section></div></section>
<section class="research-overview" id="research"><div class="container"><div class="section-title-row"><h2><a href="research/index.html">Research Themes</a></h2><div class="research-heading-actions"><div class="research-controls" aria-label="研究テーマのスライド操作"><button type="button" data-research-prev aria-label="前の研究テーマ">←</button><button type="button" data-research-next aria-label="次の研究テーマ">→</button></div><a href="research/index.html">すべて見る →</a></div></div><div class="research-slider" data-research-slider tabindex="0" aria-label="研究テーマ一覧">{research_cards}</div></div></section>
<section class="overview-bottom"><div class="container overview-columns"><section class="overview-block" id="works"><div class="section-mini-head"><h2>Selected Works</h2><a href="works.html">すべての業績を見る →</a></div><div class="publication-list">{_selected_works(all_works, 3)}</div></section>
<section class="overview-block" id="teaching"><div class="section-mini-head"><h2>Teaching</h2><a href="teaching.html">すべて見る →</a></div><div class="teaching-list">{render_teaching_cards(teaching_rows, 4)}</div></section></div></section>
<section class="profile-section" id="profile"><div class="container profile-identity"><div class="profile-identity-main">{profile_image}<div><p class="eyebrow">Profile</p><h2>{esc(p["nameJa"])} <span>{esc(p["nameEn"])}</span></h2><p class="profile-affiliation">{esc(p["affiliation"])}　{esc(p["position"])}</p><div class="profile-links">{external_links}</div></div></div></div><div class="container profile-section-grid"><div><h3>Profile Details</h3><dl class="fact-list">{fact_html}</dl></div><div><h3>Career</h3><div>{_history(p.get("history", []))}</div></div></div></section>
<section class="contact-section" id="contact"><div class="container contact-grid"><div class="contact-info"><p class="eyebrow">Contact</p><h2>お問い合わせ</h2><p class="contact-lead">研究、共同研究、教育活動などに関するご連絡はこちらからお願いします。</p><dl class="contact-details"><div><dt>Email</dt><dd>{esc(contact.get("displayEmail", ""))}</dd></div><div><dt>Affiliation</dt><dd>{esc(contact.get("institution", ""))}</dd></div><div><dt>Location</dt><dd>{esc(contact.get("postalCode", ""))}<br>{esc(contact.get("address", ""))}<br><a href="{esc(contact.get("mapsUrl", ""))}" target="_blank" rel="noopener noreferrer">Google Mapsで見る ↗</a></dd></div></dl></div>
<form class="contact-form" data-contact-form data-email-user="{esc(contact.get("emailUser", ""))}" data-email-domain="{esc(contact.get("emailDomain", ""))}"><label>お名前<input name="name" autocomplete="name" required></label><label>返信先メールアドレス<input name="email" type="email" autocomplete="email" required></label><label>件名<input name="subject" required></label><label>本文<textarea name="message" rows="7" required></textarea></label><div class="contact-form-actions"><button type="submit">メールを作成 →</button><p>送信ボタンを押すと、端末のメールアプリが開きます。</p></div></form></div></section>
</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''
