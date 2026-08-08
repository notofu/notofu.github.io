#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from content_module import CONTENT_CATEGORIES, build_content_detail, build_research_index, load_content_items
from home_module import build_contact_page, build_home
from image_pipeline import prepare_content_images, prepare_profile_image
from news_module import build_news_detail, build_news_index, legacy_news_items, load_news
from researchmap_sync import normalized_misc_and_presentations, normalized_publications, sync_researchmap
from seo_tools import build_feed, build_sitemap, fail_on_errors, validate_dist, validate_source
from teaching_module import build_teaching_page
from works_module import build_works_page

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CONTENT_PATH = ROOT / "content.json"


def copy_static() -> None:
    for name in ["styles.css", "script.js", ".nojekyll"]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, DIST / name)
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", DIST / "assets", dirs_exist_ok=True)
    # Search Console verification files must remain at the public site root.
    for verification_file in ROOT.glob("google*.html"):
        shutil.copy2(verification_file, DIST / verification_file.name)


def main() -> None:
    data = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    site_url = data["site"]["url"].rstrip("/") + "/"
    permalink = (data.get("researchmap") or {}).get("permalink", "notokaede")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    copy_static()

    # Content files are local and deterministic. Validate them before rendering.
    content_items = load_content_items(ROOT, data)
    news_items = load_news(ROOT) or legacy_news_items(data)
    fail_on_errors(validate_source(ROOT, content_items, news_items))

    # Images are generated only in dist/. The repository keeps the original master files.
    prepare_profile_image(ROOT, DIST, data)
    prepare_content_images(ROOT, DIST, content_items)

    # researchmap is fetched once at build time, not in each visitor's browser.
    rm_data, rm_warnings = sync_researchmap(ROOT, permalink=permalink)
    for warning in rm_warnings:
        print(f"[researchmap] {warning}")

    works_html, all_works = build_works_page(data, rm_data, permalink=permalink)
    teaching_html, teaching_rows = build_teaching_page(data, rm_data, permalink=permalink)

    # Top page uses the same build-time data, so it opens immediately without API waits.
    (DIST / "index.html").write_text(build_home(data, content_items, news_items, all_works, teaching_rows), encoding="utf-8")
    (DIST / "works.html").write_text(works_html, encoding="utf-8")
    (DIST / "teaching.html").write_text(teaching_html, encoding="utf-8")
    (DIST / "contact.html").write_text(build_contact_page(data), encoding="utf-8")

    (DIST / "research").mkdir(exist_ok=True)
    (DIST / "research" / "index.html").write_text(build_research_index(data, content_items), encoding="utf-8")
    for category in CONTENT_CATEGORIES:
        (DIST / CONTENT_CATEGORIES[category]["dir"]).mkdir(exist_ok=True)
    for item in content_items:
        target = DIST / item["url"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_content_detail(data, item, all_works), encoding="utf-8")

    news_dir = DIST / "news"
    news_dir.mkdir(exist_ok=True)
    (news_dir / "index.html").write_text(build_news_index(data, news_items), encoding="utf-8")
    for item in news_items:
        if item.get("url", "").startswith("news/"):
            target = DIST / item["url"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(build_news_detail(data, item), encoding="utf-8")

    # Feed: News + Blog. Sitemap: every public page, with lastmod where content has a date.
    (DIST / "feed.xml").write_text(build_feed(data["site"], news_items, content_items), encoding="utf-8")
    entries = [
        {"url": site_url, "lastmod": date.today().isoformat()},
        {"url": urljoin(site_url, "works.html"), "lastmod": date.today().isoformat()},
        {"url": urljoin(site_url, "teaching.html"), "lastmod": date.today().isoformat()},
        {"url": urljoin(site_url, "contact.html"), "lastmod": date.today().isoformat()},
        {"url": urljoin(site_url, "research/"), "lastmod": date.today().isoformat()},
        {"url": urljoin(site_url, "news/"), "lastmod": news_items[0].get("date") if news_items else date.today().isoformat()},
    ]
    entries.extend({"url": urljoin(site_url, x["url"]), "lastmod": x.get("updated") or x.get("date") or ""} for x in content_items)
    entries.extend({"url": urljoin(site_url, x["url"]), "lastmod": x.get("date") or ""} for x in news_items if x.get("url", "").startswith("news/"))
    (DIST / "sitemap.xml").write_text(build_sitemap(site_url, entries), encoding="utf-8")
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {urljoin(site_url, 'sitemap.xml')}\n",
        encoding="utf-8",
    )

    # Catch missing files / broken internal links before GitHub Pages deploys them.
    fail_on_errors(validate_dist(DIST))
    print(f"[build] OK: {len(content_items)} content items, {len(news_items)} news items, {len(all_works)} works")


if __name__ == "__main__":
    main()
