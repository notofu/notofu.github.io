from __future__ import annotations

import urllib.parse
from urllib.parse import urljoin

from researchmap_sync import (
    localized, names, normalized_misc_and_presentations, normalized_publications,
    period_from_to, format_period,
)
from site_common import esc, favicon_links, header, og_meta


def _rm_url(permalink: str, resource: str, item: dict) -> str:
    rid = item.get("rm:id") or item.get("id")
    base = f"https://researchmap.jp/{urllib.parse.quote(permalink)}/{resource}"
    return f"{base}/{urllib.parse.quote(str(rid))}" if rid else base


def _output_kind(type_text: str) -> tuple[str, str]:
    t = str(type_text or "")
    low = t.lower()
    if t == "paper" or "査読" in t or ("論文" in t and "国際" not in t): return "journal", "論文"
    if "conference" in low or "国際会議" in t: return "conference", "国際会議"
    if t == "presentation" or "発表" in t or "研究会" in t: return "presentation", "発表"
    if t == "misc": return "report", "MISC"
    return "other", t or "業績"


def _output_rows(records: list[dict]) -> str:
    rows = []
    for row in records:
        kind, label = _output_kind(row.get("type", ""))
        title = esc(row.get("title", ""))
        if row.get("url"):
            title = f'<a href="{esc(row["url"])}" target="_blank" rel="noopener noreferrer">{title}</a>'
        meta = " / ".join(x for x in [row.get("authors", ""), row.get("venue", "")] if x)
        rows.append(
            f'<article class="output-row" data-kind="{kind}">'
            f'<div class="output-year">{esc(row.get("year", ""))}</div>'
            f'<div class="output-type"><span class="work-kind-square" aria-hidden="true"></span>{esc(label)}</div>'
            f'<div class="output-content"><h3>{title}</h3><p>{esc(meta)}</p></div></article>'
        )
    return "".join(rows) or '<p class="works-empty">現在、公開中の項目はありません。</p>'


def _project_role(value: str) -> str:
    return {
        "principal_investigator": "研究代表",
        "coinvestigator": "研究分担",
        "coinvestigator_not_use_grants": "連携研究者",
        "others": "その他",
    }.get(value, "研究課題")


def _property_type(value: str) -> str:
    return {
        "patent_right": "特許", "utility_model_right": "実用新案",
        "design_right": "意匠", "trademark": "商標",
    }.get(value, "産業財産権")


def _academic_roles(value) -> str:
    labels = {
        "planning_etc": "企画・運営", "panel_chair_etc": "座長等", "supervision": "監修",
        "review": "審査・評価", "academic_research_planning": "学術調査", "peer_review": "査読",
        "save_or_restore": "保存・修復", "others": "その他",
    }
    values = value if isinstance(value, list) else ([value] if value else [])
    return "・".join(labels.get(x, str(x)) for x in values if x) or "学術貢献"


def _activity_row(period: str, badge: str, title: str, meta: str, description: str, url: str, kind: str) -> str:
    title_html = esc(title or "タイトル未登録")
    if url:
        title_html = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{title_html}</a>'
    desc = f'<p class="rmap-achievement-description">{esc(description)}</p>' if description else ""
    return (
        f'<article class="rmap-achievement-row" data-kind="{esc(kind)}">'
        f'<div class="rmap-achievement-period">{esc(period or "—")}</div>'
        f'<div class="rmap-achievement-badge">{esc(badge)}</div>'
        f'<div class="rmap-achievement-body"><h3>{title_html}</h3>'
        f'<p class="rmap-achievement-meta">{esc(meta)}</p>{desc}</div>'
        '<div class="rmap-achievement-arrow" aria-hidden="true">↗</div></article>'
    )


def _projects(items: list[dict], permalink: str) -> str:
    rows = []
    for item in items:
        identifiers = item.get("identifiers") if isinstance(item.get("identifiers"), dict) else {}
        grant = identifiers.get("grant_number", "")
        if isinstance(grant, list): grant = grant[0] if grant else ""
        meta = " / ".join(x for x in [localized(item.get("offer_organization")), localized(item.get("system_name")), localized(item.get("category")), f"課題番号 {grant}" if grant else ""] if x)
        rows.append(_activity_row(period_from_to(item.get("from_date"), item.get("to_date")), _project_role(item.get("research_project_owner_role", "")), localized(item.get("research_project_title")), meta, localized(item.get("description")), _rm_url(permalink, "research_projects", item), "project"))
    return "".join(rows) or '<p class="works-empty">現在、公開中の研究課題はありません。</p>'


def _property(items: list[dict], permalink: str) -> str:
    rows = []
    for item in items:
        number = item.get("patent_number") or item.get("patent_announcement_number") or item.get("application_number") or item.get("patent_publication_number") or ""
        dt = item.get("registration_date") or item.get("patent_announcement_date") or item.get("application_date") or item.get("patent_publication_date") or ""
        meta = " / ".join(x for x in [str(number), localized(item.get("right_holder"))] if x)
        rows.append(_activity_row(format_period(dt), _property_type(item.get("industrial_property_right_type", "")), localized(item.get("industrial_property_right_title")), meta, localized(item.get("description")), _rm_url(permalink, "industrial_property_rights", item), "property"))
    return "".join(rows) or '<p class="works-empty">現在、公開中の産業財産権はありません。</p>'


def _academic(items: list[dict], permalink: str) -> str:
    rows = []
    for item in items:
        meta = " / ".join(x for x in [localized(item.get("promoter")), localized(item.get("location"))] if x)
        rows.append(_activity_row(period_from_to(item.get("from_event_date"), item.get("to_event_date"), ""), _academic_roles(item.get("academic_contribution_roles")), localized(item.get("academic_contribution_title")), meta, localized(item.get("description")), _rm_url(permalink, "academic_contribution", item), "academic"))
    return "".join(rows) or '<p class="works-empty">現在、公開中の学術貢献活動はありません。</p>'


def build_works_page(data: dict, rm_data: dict[str, list[dict]], permalink: str = "notokaede") -> tuple[str, list[dict]]:
    site, p = data["site"], data["profile"]
    papers = normalized_publications(rm_data)
    misc = normalized_misc_and_presentations(rm_data)
    projects = rm_data.get("research_projects", [])
    property_items = rm_data.get("industrial_property_rights", [])
    academic = rm_data.get("academic_contribution", [])
    canonical = urljoin(site["url"], "works.html")
    desc = "論文、国際会議、研究発表、研究課題、産業財産権、学術貢献活動を掲載しています。"
    source_note = 'researchmapの公開情報をGitHub Actionsのビルド時に取得しています。'
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Works | noto Lab</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(canonical)}">{favicon_links()}
{og_meta(site, "Works | noto Lab", desc, canonical)}<link rel="stylesheet" href="styles.css?v=20260808h"><script src="script.js?v=20260808h" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="works")}<main id="main">
<section class="hero works-hero"><div class="container"><a class="back-link" href="index.html">← トップページへ戻る</a><p class="eyebrow">Research Outputs &amp; Activities</p><h1>Works</h1><p>{esc(desc)}</p><p class="works-source-note">{esc(source_note)}</p>
<nav class="works-local-nav" aria-label="Worksページ内メニュー"><a href="#publications">Publications</a><a href="#presentations">Presentations &amp; MISC</a><a href="#projects">Projects &amp; Grants</a><a href="#ip">Intellectual Property</a><a href="#service">Academic Service</a></nav></div></section>
<section class="section" id="publications"><div class="container"><div class="works-section-title"><div><h2>論文・国際会議</h2><p class="section-label">PUBLICATIONS</p></div><p class="section-intro">査読論文・国際会議論文など。</p></div><div class="output-list">{_output_rows(papers)}</div></div></section>
<section class="section section--soft" id="presentations"><div class="container"><div class="works-section-title"><div><h2>研究発表・MISC</h2><p class="section-label">PRESENTATIONS &amp; MISC</p></div></div><div class="output-list">{_output_rows(misc)}</div></div></section>
<section class="section" id="projects"><div class="container"><div class="works-section-title"><div><h2>共同研究・競争的資金等の研究課題</h2><p class="section-label">PROJECTS &amp; GRANTS</p></div></div><div class="rmap-achievement-list">{_projects(projects, permalink)}</div></div></section>
<section class="section section--soft" id="ip"><div class="container"><div class="works-section-title"><div><h2>産業財産権</h2><p class="section-label">INTELLECTUAL PROPERTY</p></div></div><div class="rmap-achievement-list">{_property(property_items, permalink)}</div></div></section>
<section class="section" id="service"><div class="container"><div class="works-section-title"><div><h2>学術貢献活動</h2><p class="section-label">ACADEMIC SERVICE</p></div></div><div class="rmap-achievement-list">{_academic(academic, permalink)}</div></div></section>
<section class="section section--soft"><div class="container"><a class="text-link" href="https://researchmap.jp/{esc(permalink)}" target="_blank" rel="noopener noreferrer">researchmapで全登録情報を見る ↗</a></div></section>
</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''
    return html, papers + misc
