from __future__ import annotations

from urllib.parse import urljoin

from researchmap_sync import localized, period_from_to
from site_common import esc, favicon_links, header, og_meta, section_icon


def teaching_records(rm_data: dict[str, list[dict]], fallback: list[dict]) -> list[dict]:
    rows = []
    for item in rm_data.get("teaching_experience", []):
        rows.append({
            "period": period_from_to(item.get("from_date"), item.get("to_date")),
            "title": localized(item.get("subject_name")) or "科目名未登録",
            "institution": localized(item.get("institution_name")),
            "description": localized(item.get("description")),
        })
    if rows:
        rows.sort(key=lambda x: (x.get("period", ""), x.get("title", "")), reverse=True)
        return rows
    return [{"period": "掲載中", "title": x.get("title", ""), "institution": "", "description": x.get("description", "")} for x in fallback]


def render_teaching_cards(items: list[dict], limit: int = 4) -> str:
    rows = []
    for item in items[:limit]:
        rows.append(
            '<article class="teaching-item">'
            f'<h3>{esc(item.get("title", ""))}</h3>'
            f'<p>{esc(item.get("institution") or item.get("description", ""))}</p></article>'
        )
    return "".join(rows)


def build_teaching_page(data: dict, rm_data: dict[str, list[dict]], permalink: str = "notokaede") -> tuple[str, list[dict]]:
    site, p = data["site"], data["profile"]
    rows = teaching_records(rm_data, data.get("teaching", {}).get("items", []))
    rendered = []
    for item in rows:
        inst = f'<p class="teaching-course-institution">{esc(item.get("institution", ""))}</p>' if item.get("institution") else ""
        desc = f'<p class="teaching-course-description">{esc(item.get("description", ""))}</p>' if item.get("description") else ""
        rendered.append(
            '<article class="teaching-course"><div class="teaching-course-period">'
            f'{esc(item.get("period", ""))}</div><div class="teaching-course-main"><h2>{esc(item.get("title", ""))}</h2>{inst}{desc}</div></article>'
        )
    canonical = urljoin(site["url"], "teaching.html")
    desc = f'{p["nameJa"]}の担当科目・教育活動。'
    html = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Teaching | noto Lab</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(canonical)}">{favicon_links()}
{og_meta(site, "Teaching | noto Lab", desc, canonical)}<link rel="stylesheet" href="styles.css?v=20260808k"><script src="script.js?v=20260808i" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, active="teaching")}<main id="main">
<section class="works-hero teaching-hero"><div class="container"><a class="back-link" href="index.html">← トップページへ戻る</a><p class="eyebrow">Education</p><h1 class="page-heading-with-icon">{section_icon("teaching")}<span>Teaching</span></h1><p>担当科目・教育活動を掲載しています。</p><div class="teaching-source-row"><span>researchmapの公開情報をビルド時に反映</span><a href="https://researchmap.jp/{esc(permalink)}/teaching_experience" target="_blank" rel="noopener noreferrer">researchmapで確認する ↗</a></div></div></section>
<section class="teaching-page-section"><div class="container teaching-page-grid"><aside class="teaching-page-aside"><p class="section-label">COURSES</p><h2>担当科目</h2><p>科目名、担当機関、担当期間を掲載しています。</p></aside><div class="teaching-course-list">{''.join(rendered)}</div></div></section>
</main><footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="index.html">トップページへ戻る ←</a></div></footer></body></html>'''
    return html, rows
