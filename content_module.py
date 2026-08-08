from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from markdown_utils import markdown_to_html_with_toc
from site_common import esc, favicon_links, header, is_external, local_url, og_meta, shorten

CONTENT_CATEGORIES = {
    "research": {"label": "研究テーマ", "badge": "Research", "class": "research", "dir": "research"},
    "graduation": {"label": "卒業研究", "badge": "Student Project", "class": "graduation", "dir": "graduation"},
    "blog": {"label": "Blog", "badge": "Blog", "class": "blog", "dir": "blog"},
}


def _front_value(value: str):
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    low = value.lower()
    if low in {"true", "yes", "on"}: return True
    if low in {"false", "no", "off"}: return False
    if re.fullmatch(r"-?\d+", value): return int(value)
    if value.startswith("[") and value.endswith("]"):
        return [x.strip().strip('"\'') for x in value[1:-1].split(",") if x.strip()]
    return value


def parse_markdown_file(root: Path, path: Path, category: str) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta: dict[str, object] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = _front_value(value)
    if meta.get("published", True) is False:
        return None
    cat = str(meta.get("category", category)).strip().lower()
    if cat not in CONTENT_CATEGORIES:
        cat = category
    cfg = CONTENT_CATEGORIES[cat]
    title = str(meta.get("title", path.stem)).strip()
    summary = str(meta.get("summary", "")).strip()
    image = str(meta.get("image", "")).strip()
    thumbnail = str(meta.get("thumbnail", "")).strip()
    fallback = not image
    if fallback:
        image = "assets/favicon.svg"
    if not thumbnail:
        thumbnail = image
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(",") if x.strip()]
    related = meta.get("relatedWorks", meta.get("related", []))
    if isinstance(related, str):
        related = [x.strip() for x in related.split(",") if x.strip()]
    try:
        order = int(meta.get("order", 9999))
    except (TypeError, ValueError):
        order = 9999
    return {
        "title": title,
        "summary": summary,
        "description": summary,
        "image": image,
        "thumbnail": thumbnail,
        "_thumbnailSource": thumbnail,
        "imageAlt": str(meta.get("imageAlt", "noto Lab" if fallback else f"{title}のサムネイル")),
        "date": str(meta.get("date", "")).strip(),
        "updated": str(meta.get("updated", "")).strip(),
        "tags": tags,
        "relatedWorks": related,
        "order": order,
        "slug": path.stem,
        "category": cat,
        "categoryLabel": cfg["label"],
        "categoryBadge": cfg["badge"],
        "categoryClass": cfg["class"],
        "url": f'{cfg["dir"]}/{path.stem}.html',
        "bodyMarkdown": parts[2].lstrip("\n"),
        "_imageFallback": fallback,
        "sourcePath": str(path.relative_to(root)),
    }


def _fallback_research_items(data: dict) -> list[dict]:
    items = []
    defaults = ["music-cognition", "performance", "gaze", "ensemble"]
    for i, raw in enumerate(data.get("research", {}).get("areas", [])):
        slug = str(raw.get("slug") or (defaults[i] if i < len(defaults) else f"theme-{i+1}"))
        image = str(raw.get("image") or "assets/favicon.svg")
        fallback = not bool(raw.get("image"))
        items.append({
            "title": raw.get("title", ""), "summary": raw.get("description", ""),
            "description": raw.get("description", ""), "image": image, "thumbnail": image,
            "_thumbnailSource": image, "imageAlt": raw.get("imageAlt") or ("noto Lab" if fallback else f'{raw.get("title", "研究テーマ")}のサムネイル'),
            "date": "", "updated": "", "tags": raw.get("tags", []), "relatedWorks": [],
            "order": i + 1, "slug": slug, "category": "research", "categoryLabel": "研究テーマ",
            "categoryBadge": "Research", "categoryClass": "research", "url": f"research/{slug}.html",
            "bodyMarkdown": f'## 研究概要\n\n{raw.get("description", "")}\n\n## 研究内容\n\n詳しい説明、図、関連論文などは順次追加予定です。',
            "_imageFallback": fallback, "sourcePath": "content.json",
        })
    return items


def load_content_items(root: Path, data: dict | None = None) -> list[dict]:
    items: list[dict] = []
    contents = root / "contents"
    for category in CONTENT_CATEGORIES:
        folder = contents / category
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.name.startswith("_") or path.name.lower() == "readme.md":
                continue
            item = parse_markdown_file(root, path, category)
            if item:
                items.append(item)
    if data is not None and not any(x["category"] == "research" for x in items):
        items.extend(_fallback_research_items(data))
    research = sorted([x for x in items if x["category"] == "research"], key=lambda x: (x.get("order", 9999), x["title"]))
    others: list[dict] = []
    for category in ("graduation", "blog"):
        group = [x for x in items if x["category"] == category]
        group.sort(key=lambda x: (x.get("date", ""), -x.get("order", 9999)), reverse=True)
        others.extend(group)
    return research + others


def render_category_badge(item: dict) -> str:
    return f'<span class="content-badge content-badge--{esc(item["categoryClass"])}"><span aria-hidden="true"></span>{esc(item["categoryBadge"])}</span>'


def render_content_cards(items: list[dict], prefix: str = "", include_category: bool = True) -> str:
    cards = []
    for item in items:
        url = local_url(item["url"], prefix)
        small = local_url(item.get("thumbnailSmall") or item.get("thumbnail") or item["image"], prefix)
        large = local_url(item.get("thumbnailLarge") or item.get("thumbnail") or item["image"], prefix)
        fallback = " research-thumb--fallback" if item.get("_imageFallback") else ""
        meta = render_category_badge(item) if include_category else ""
        if item.get("date"):
            meta += f'<time datetime="{esc(item["date"])}">{esc(item["date"].replace("-", "."))}</time>'
        cards.append(
            '<article class="research-card content-card">'
            f'<a class="research-thumb-link" href="{esc(url)}" aria-label="{esc(item["title"])}の詳細を見る">'
            f'<img class="research-thumb{fallback}" src="{esc(small)}" srcset="{esc(small)} 320w, {esc(large)} 640w" sizes="(max-width: 760px) 112px, 220px" alt="{esc(item["imageAlt"])}" width="320" height="180" loading="lazy" decoding="async" fetchpriority="low">'
            '</a><div class="research-card-copy">'
            f'<h3><a href="{esc(url)}">{esc(item["title"])}</a></h3>'
            f'<div class="content-card-meta">{meta}</div>'
            f'<p>{esc(shorten(item.get("summary", ""), 54))}</p>'
            '</div></article>'
        )
    return "".join(cards)


def render_content_row(category: str, items: list[dict], prefix: str = "../") -> str:
    cfg = CONTENT_CATEGORIES[category]
    cards = render_content_cards(items, prefix=prefix, include_category=True)
    if not cards:
        cards = '<div class="content-empty">現在、公開中の記事はありません。</div>'
    controls = ""
    if len(items) > 1:
        controls = (
            f'<div class="content-row-controls" aria-label="{esc(cfg["label"])}のスライド操作">'
            '<button type="button" data-content-prev aria-label="前へ">←</button>'
            '<button type="button" data-content-next aria-label="次へ">→</button></div>'
        )
    return (
        f'<section class="content-row content-row--{esc(cfg["class"])}" id="{esc(category)}" data-content-row>'
        '<div class="content-row-head"><div><span class="content-row-mark" aria-hidden="true"></span>'
        f'<h2>{esc(cfg["label"])}</h2><span class="content-count">{len(items)}</span></div>{controls}</div>'
        f'<div class="content-row-slider" data-content-slider tabindex="0" aria-label="{esc(cfg["label"])}一覧">{cards}</div></section>'
    )


def related_works(item: dict, works: list[dict], limit: int = 4) -> list[dict]:
    keys = [str(x).lower() for x in item.get("relatedWorks", []) if str(x).strip()]
    if not keys:
        keys = [str(x).lower() for x in item.get("tags", []) if len(str(x)) >= 3]
    if not keys:
        return []
    scored = []
    for work in works:
        hay = " ".join(str(work.get(k, "")) for k in ("title", "venue", "authors", "type")).lower()
        score = sum(1 for key in keys if key in hay)
        if score:
            scored.append((score, work))
    # 表示順は発表年の新しい順。同一年では関連度の高い業績を先にする。
    def year_value(work: dict) -> int:
        raw = str(work.get("year", ""))
        m = re.search(r"(?:19|20)\d{2}", raw)
        return int(m.group(0)) if m else 0

    scored.sort(key=lambda x: (year_value(x[1]), x[0]), reverse=True)
    return [x[1] for x in scored[:limit]]


def _related_work_kind(type_text: str) -> tuple[str, str]:
    """Worksページと同じ分類名・色に揃える。"""
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


def _related_html(rows: list[dict]) -> str:
    if not rows:
        return ""
    items = []
    for row in rows:
        kind, label = _related_work_kind(row.get("type", ""))
        title = esc(row.get("title", ""))
        if row.get("url"):
            title = f'<a href="{esc(row["url"])}" target="_blank" rel="noopener noreferrer">{title}</a>'
        meta = " / ".join(x for x in [row.get("authors", ""), row.get("venue", "")] if x)
        items.append(
            f'<article class="related-work" data-kind="{esc(kind)}">'
            f'<div class="related-work-year">{esc(row.get("year", ""))}</div>'
            f'<div class="output-type">{esc(label)}</div>'
            f'<div class="related-work-content"><h3>{title}</h3><p>{esc(meta)}</p></div>'
            '</article>'
        )
    return '<section class="article-related"><h2>関連する研究業績</h2>' + ''.join(items) + '</section>'


def build_content_detail(data: dict, item: dict, all_works: list[dict]) -> str:
    site, p = data["site"], data["profile"]
    canonical = urljoin(site["url"], item["url"])
    body, toc = markdown_to_html_with_toc(item.get("bodyMarkdown", ""), prefix="../")
    image = item.get("detailImage") or item["image"]
    image = local_url(image, "../")
    full_image = local_url(item.get("image", ""), "../")
    fallback_class = " article-hero-image--fallback" if item.get("_imageFallback") else ""
    zoom_class = "" if item.get("_imageFallback") else " is-zoomable"
    zoom_attrs = "" if item.get("_imageFallback") else (
        f' data-lightbox-src="{esc(full_image)}"'
        f' data-lightbox-alt="{esc(item["imageAlt"])}"'
        ' tabindex="0" role="button" aria-label="画像を拡大表示"'
    )
    tags = ''.join(f'<span>{esc(tag)}</span>' for tag in item.get("tags", []))
    date_html = f'<time datetime="{esc(item["date"])}">{esc(item["date"].replace("-", "."))}</time>' if item.get("date") else ""
    toc_html = ""
    if len(toc) >= 2:
        toc_html = '<nav class="article-toc" aria-label="ページ内目次"><strong>Contents</strong><ol>' + ''.join(
            f'<li><a href="#{esc(section_id)}">{esc(label)}</a></li>' for section_id, label in toc
        ) + '</ol></nav>'
    rel = _related_html(related_works(item, all_works))
    og_image = item.get("detailImage") if not item.get("_imageFallback") else None
    title = f'{item["title"]} | noto Lab'
    description = item.get("summary", "") or item["title"]
    return f'''<!doctype html><html lang="ja"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<link rel="canonical" href="{esc(canonical)}">{favicon_links("../")}
{og_meta(site, title, description, canonical, og_image, "article")}
<link rel="stylesheet" href="../styles.css?v=20260808h"><script src="../script.js?v=20260808h" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, prefix="../", active="research")}
<main id="main"><article class="article-page"><div class="container article-container">
<p class="breadcrumb"><a href="../index.html">Home</a> / <a href="../research/index.html">Research</a> / {esc(item["categoryLabel"])}</p>
<div class="article-meta-row">{render_category_badge(item)}{date_html}</div><h1>{esc(item["title"])}</h1>
<p class="article-lead">{esc(item.get("summary", ""))}</p>
<div class="article-hero-image{fallback_class}"><img class="article-detail-image{zoom_class}" src="{esc(image)}" alt="{esc(item["imageAlt"])}" decoding="async"{zoom_attrs}></div>
<div class="article-tags">{tags}</div>{toc_html}<div class="article-body">{body}</div>{rel}
<div class="article-back"><a href="../research/index.html">← 一覧へ戻る</a></div></div></article></main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''


def build_research_index(data: dict, content_items: list[dict]) -> str:
    site, p = data["site"], data["profile"]
    canonical = urljoin(site["url"], "research/")
    groups = {category: [x for x in content_items if x["category"] == category] for category in CONTENT_CATEGORIES}
    rows = ''.join(render_content_row(category, groups[category]) for category in ("research", "graduation", "blog"))
    desc = "研究テーマ、卒業研究、Blogの記事一覧です。"
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research | noto Lab</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><link rel="canonical" href="{esc(canonical)}">{favicon_links("../")}
{og_meta(site, "Research | noto Lab", desc, canonical)}<link rel="stylesheet" href="../styles.css?v=20260808h"><script src="../script.js?v=20260808h" defer></script></head><body>
<a class="skip-link" href="#main">本文へ移動</a>{header(p, prefix="../", active="research")}
<main id="main"><section class="works-hero content-hub-hero"><div class="container"><a class="back-link" href="../index.html">← トップページへ戻る</a><p class="eyebrow">noto Lab</p><h1>Research</h1><p>研究テーマ、卒業研究、Blogをまとめています。気になる項目から詳細をご覧ください。</p>
<nav class="content-filter-nav" aria-label="コンテンツカテゴリ"><a href="#research">研究テーマ <span>{len(groups['research'])}</span></a><a href="#graduation">卒業研究 <span>{len(groups['graduation'])}</span></a><a href="#blog">Blog <span>{len(groups['blog'])}</span></a></nav></div></section>
<section class="content-hub"><div class="container">{rows}</div></section></main>
<footer class="site-footer"><div class="container footer-inner"><p>© <span data-current-year></span> {esc(p["nameEn"])}</p><a href="#top">ページ上部へ戻る ↑</a></div></footer></body></html>'''
