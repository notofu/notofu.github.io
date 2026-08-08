from __future__ import annotations

import html
import re

from site_common import esc, is_external, local_url


def inline_markdown(text: str, prefix: str = "") -> str:
    escaped = esc(text)

    def image_repl(match):
        alt, url = match.group(1), html.unescape(match.group(2))
        image_url = esc(local_url(url, prefix))
        label = alt or "記事内画像"
        return (
            f'<img class="article-inline-image is-zoomable" src="{image_url}" '
            f'alt="{alt}" loading="lazy" decoding="async" '
            f'data-lightbox-src="{image_url}" data-lightbox-alt="{alt}" '
            f'tabindex="0" role="button" aria-label="{label}を拡大表示">'
        )

    escaped = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_repl, escaped)

    def link_repl(match):
        label, url = match.group(1), html.unescape(match.group(2))
        target = ' target="_blank" rel="noopener noreferrer"' if is_external(url) else ''
        return f'<a href="{esc(local_url(url, prefix))}"{target}>{label}</a>'

    escaped = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    return escaped


def markdown_to_html_with_toc(text: str, prefix: str = "") -> tuple[str, list[tuple[str, str]]]:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []
    toc: list[tuple[str, str]] = []
    section_no = 0

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            joined = " ".join(x.strip() for x in paragraph)
            out.append(f'<p>{inline_markdown(joined, prefix)}</p>')
            paragraph = []

    def flush_list():
        nonlocal list_type, list_items
        if list_type and list_items:
            tag = "ol" if list_type == "ol" else "ul"
            out.append(f'<{tag}>' + ''.join(f'<li>{inline_markdown(x, prefix)}</li>' for x in list_items) + f'</{tag}>')
        list_type = None
        list_items = []

    for raw in lines + [""]:
        stripped = raw.strip()
        if not stripped:
            flush_paragraph(); flush_list(); continue
        if stripped in {"---", "***"}:
            flush_paragraph(); flush_list(); out.append("<hr>"); continue
        m = re.match(r'^(#{2,4})\s+(.+)$', stripped)
        if m:
            flush_paragraph(); flush_list()
            level = len(m.group(1))
            section_no += 1
            section_id = f"section-{section_no}"
            label = re.sub(r'[`*_\[\]()]', '', m.group(2)).strip()
            if level == 2:
                toc.append((section_id, label))
            out.append(f'<h{level} id="{section_id}">{inline_markdown(m.group(2), prefix)}</h{level}>')
            continue
        if stripped.startswith("> "):
            flush_paragraph(); flush_list(); out.append(f'<blockquote>{inline_markdown(stripped[2:], prefix)}</blockquote>'); continue
        m = re.match(r'^[-*]\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if list_type not in {None, "ul"}: flush_list()
            list_type = "ul"; list_items.append(m.group(1)); continue
        m = re.match(r'^\d+\.\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if list_type not in {None, "ol"}: flush_list()
            list_type = "ol"; list_items.append(m.group(1)); continue
        paragraph.append(stripped)
    return "".join(out), toc


def markdown_to_html(text: str, prefix: str = "") -> str:
    return markdown_to_html_with_toc(text, prefix)[0]
