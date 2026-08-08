from __future__ import annotations

import http.client
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.researchmap.jp"
RESOURCE_TYPES = (
    "published_papers",
    "misc",
    "presentations",
    "research_projects",
    "industrial_property_rights",
    "academic_contribution",
    "teaching_experience",
)


def localized(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("ja") or value.get("en") or "").strip()
    return str(value).strip()


def names(value) -> str:
    if not value:
        return ""
    if isinstance(value, dict):
        value = value.get("ja") or value.get("en") or []
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or localized(item)
            else:
                name = str(item)
            if name:
                result.append(str(name).strip())
        return ", ".join(result)
    return str(value)


def extract_items(payload) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "@graph"):
        if isinstance(payload.get(key), list):
            return [x for x in payload[key] if isinstance(x, dict)]
    return []


def fetch_resource(permalink: str, resource: str, limit: int = 100, retries: int = 3) -> list[dict]:
    query = urllib.parse.urlencode({"limit": limit})
    url = f"{API_BASE}/{urllib.parse.quote(permalink)}/{resource}?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, application/ld+json;q=0.9, */*;q=0.1",
            "User-Agent": "noto-lab-site-builder/1.0 (+https://notofu.github.io/)",
        },
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return [x for x in extract_items(payload) if x.get("display") != "hidden"]
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            socket.timeout,
            ConnectionError,
            OSError,
            http.client.HTTPException,
            json.JSONDecodeError,
        ) as exc:
            # researchmap occasionally resets a TLS connection or closes it
            # before a response is complete. Treat those as temporary API
            # failures: retry here, then let sync_researchmap() fall back
            # without aborting the whole GitHub Pages build.
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"researchmap fetch failed: {resource}: {last_error}")


def sync_researchmap(root: Path, permalink: str = "notokaede") -> tuple[dict[str, list[dict]], list[str]]:
    data: dict[str, list[dict]] = {}
    offline = os.environ.get("RESEARCHMAP_OFFLINE", "").lower() in {"1", "true", "yes"}
    warnings: list[str] = []
    for resource in RESOURCE_TYPES:
        if offline:
            data[resource] = []
            continue
        try:
            data[resource] = fetch_resource(permalink, resource)
            print(f"[researchmap] {resource}: {len(data[resource])} records")
        except RuntimeError as exc:
            warnings.append(str(exc))
            data[resource] = []
            print(f"[researchmap] warning: {exc}")

    # Static fallback for papers/MISC keeps the site useful during an API outage.
    fallback_path = root / "data" / "researchmap_fallback.json"
    if fallback_path.exists():
        try:
            fallback = json.loads(fallback_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fallback = []
        if not data.get("published_papers"):
            data["_fallback_papers"] = [x for x in fallback if x.get("section") == "papers"]
        if not data.get("misc") and not data.get("presentations"):
            data["_fallback_misc"] = [x for x in fallback if x.get("section") == "misc"]
    return data, warnings


def date_year(value) -> str:
    text = str(value or "").strip()
    return text[:4] if len(text) >= 4 and text[:4].isdigit() else text


def format_period(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = text.replace("/", "-").split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}.{int(parts[1]):02d}"
    return text


def period_from_to(from_value, to_value, ongoing_label: str = "現在") -> str:
    f = format_period(from_value)
    t = format_period(to_value)
    if f and t:
        return f if f == t else f"{f} – {t}"
    if f:
        return f"{f} – {ongoing_label}"
    if t:
        return f"– {t}"
    return ""


def paper_record(item: dict, kind: str = "paper") -> dict:
    title = localized(item.get("paper_title")) or localized(item.get("title"))
    authors = names(item.get("authors"))
    venue = localized(item.get("publication_name")) or localized(item.get("publisher"))
    date = item.get("publication_date") or item.get("publication_year") or ""
    volume = str(item.get("volume") or item.get("volume_number") or "").strip()
    issue = str(item.get("issue") or item.get("issue_number") or "").strip()
    start = str(item.get("starting_page") or "").strip()
    end = str(item.get("ending_page") or "").strip()
    extras = []
    if volume:
        extras.append(volume + (f"({issue})" if issue else ""))
    elif issue:
        extras.append(f"({issue})")
    if start:
        extras.append(f"{start}–{end}" if end and end != start else start)
    meta_venue = ", ".join([x for x in [venue, *extras] if x])
    return {
        "year": date_year(date),
        "date": str(date),
        "type": kind,
        "title": title,
        "authors": authors,
        "venue": meta_venue,
        "url": _researchmap_record_url(item, "published_papers" if kind == "paper" else "misc"),
    }


def presentation_record(item: dict) -> dict:
    title = localized(item.get("presentation_title")) or localized(item.get("title"))
    presenters = names(item.get("presenters")) or names(item.get("authors"))
    event = localized(item.get("event")) or localized(item.get("event_name")) or localized(item.get("conference_name"))
    date = item.get("publication_date") or item.get("presentation_date") or item.get("event_date") or ""
    return {
        "year": date_year(date), "date": str(date), "type": "presentation", "title": title,
        "authors": presenters, "venue": event, "url": _researchmap_record_url(item, "presentations"),
    }


def _researchmap_record_url(item: dict, resource: str, permalink: str = "notokaede") -> str:
    rid = item.get("rm:id") or item.get("id")
    base = f"https://researchmap.jp/{permalink}/{resource}"
    return f"{base}/{urllib.parse.quote(str(rid))}" if rid else base


def normalized_publications(data: dict[str, list[dict]]) -> list[dict]:
    if data.get("published_papers"):
        records = [paper_record(x, "paper") for x in data["published_papers"]]
    else:
        records = [
            {"year": x.get("year", ""), "date": x.get("year", ""), "type": x.get("type", "paper"),
             "title": x.get("title", ""), "authors": (x.get("meta", "").split(" / ", 1) + [""])[0],
             "venue": (x.get("meta", "").split(" / ", 1) + [""])[1], "url": ""}
            for x in data.get("_fallback_papers", [])
        ]
    return sorted(records, key=lambda x: (x.get("date", ""), x.get("year", ""), x.get("title", "")), reverse=True)


def normalized_misc_and_presentations(data: dict[str, list[dict]]) -> list[dict]:
    records: list[dict] = []
    if data.get("presentations"):
        records.extend(presentation_record(x) for x in data["presentations"])
    if data.get("misc"):
        records.extend(paper_record(x, "misc") for x in data["misc"])
    if not records:
        records = [
            {"year": x.get("year", ""), "date": x.get("year", ""), "type": x.get("type", "misc"),
             "title": x.get("title", ""), "authors": (x.get("meta", "").split(" / ", 1) + [""])[0],
             "venue": (x.get("meta", "").split(" / ", 1) + [""])[1], "url": ""}
            for x in data.get("_fallback_misc", [])
        ]
    # Deduplicate obvious same-title entries if researchmap contains a record in both lists.
    seen = set(); unique = []
    for row in sorted(records, key=lambda x: (x.get("date", ""), x.get("year", ""), x.get("title", "")), reverse=True):
        key = (row.get("title", "").strip().lower(), row.get("year", ""))
        if key in seen:
            continue
        seen.add(key); unique.append(row)
    return unique
