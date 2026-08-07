from __future__ import annotations

import html
import re

from site_common import esc, is_external, local_url


def inline_markdown(text: str, prefix: str = "") -> str:
    escaped = esc(text)

    def image_repl(match):
        alt, url = match.group(1), html.unescape(match.group(2))
        return f'<img class="article-inline-image" src="{esc(local_url(url, prefix))}" alt="{alt}" loading="lazy" decoding="async">'

    escaped = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_repl, escaped)

    def link_repl(match):
        label, url = match.group(1), html.unescape(match.group(2))
        target = ' target="_blank" rel="noopener noreferrer"' if is_external(url) else ''
        return f'<a href="{esc(local_url(url, prefix))}"{target}>{label}</a>'

    escaped = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
    return escaped


def markdown_to_html(text: str, prefix: str = "") -> str:
    lines = text.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []

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
            out.append(f'<h{level}>{inline_markdown(m.group(2), prefix)}</h{level}>')
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
    return "".join(out)
