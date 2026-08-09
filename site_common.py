from __future__ import annotations

import html
from urllib.parse import urljoin, urlparse


FAVICON_VERSION = "3"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def is_external(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def href(url: str, label: str, class_name: str = "") -> str:
    if not url:
        return ""
    cls = f' class="{esc(class_name)}"' if class_name else ""
    extra = ' target="_blank" rel="noopener noreferrer"' if is_external(url) else ""
    return f'<a{cls} href="{esc(url)}"{extra}>{label}</a>'


def shorten(text: str, limit: int = 78) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("、。 ,") + "…"


def local_url(url: str, prefix: str = "") -> str:
    if not url or is_external(url) or url.startswith("#") or url.startswith("mailto:"):
        return url
    return prefix + url


def favicon_links(prefix: str = "") -> str:
    return (
        f'<link rel="icon" href="{prefix}assets/favicon.svg?v={FAVICON_VERSION}" type="image/svg+xml">\n'
        f'<link rel="shortcut icon" href="{prefix}assets/favicon.svg?v={FAVICON_VERSION}">'
    )


def section_icon(name: str, class_name: str = "page-heading-icon") -> str:
    """Render the same lightweight line icon everywhere on the site."""
    icons = {
        "research": '<rect x="4" y="5" width="7" height="6" rx="1"/><rect x="13" y="4" width="7" height="6" rx="1"/><rect x="8" y="14" width="8" height="6" rx="1"/><path d="M10 11l2 3M15 10l-2 4"/>',
        "news": '<rect x="5" y="6" width="13" height="13" rx="1.5"/><path d="M8 9h7M8 12h7M8 15h5"/><path d="M18 8h2v9a2 2 0 0 1-2 2"/>',
        "publications": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 12h6M9 15h6M9 18h4"/>',
        "teaching": '<path d="M4 5.5c3-1 5-.7 8 1.2 3-1.9 5-2.2 8-1.2v13c-3-1-5-.7-8 1.2-3-1.9-5-2.2-8-1.2z"/><path d="M12 6.7v13"/>',
        "blog": '<path d="M6 4h12v16H6z"/><path d="M9 8h6M9 11h6M9 14h4"/><path d="M16.5 4.5l3 3-6.8 6.8-3.2.7.7-3.2z"/>',
        "contact": '<path d="M4 6h16v12H4z"/><path d="M4.8 7l7.2 6 7.2-6"/>',
    }
    body = icons.get(name, icons["publications"])
    return (
        f'<svg class="{esc(class_name)}" viewBox="0 0 24 24" aria-hidden="true" focusable="false" '
        'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        f'{body}</svg>'
    )


def og_meta(site: dict, title: str, description: str, canonical: str,
            image: str | None = None, og_type: str = "website") -> str:
    image_url = image or site.get("ogImage", "assets/og-image.png")
    if image_url and not is_external(image_url):
        image_url = urljoin(site["url"], image_url)
    return f'''<meta property="og:type" content="{esc(og_type)}">
<meta property="og:locale" content="ja_JP">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(image_url)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(image_url)}">'''


def header(profile: dict, prefix: str = "", active: str = "home") -> str:
    links = [
        ("home", f"{prefix}index.html", "Home"),
        ("research", f"{prefix}research.html", "Research"),
        ("works", f"{prefix}publications.html", "Publications"),
        ("teaching", f"{prefix}teaching.html", "Teaching"),
        ("contact", f"{prefix}contact.html", "Contact"),
    ]
    nav = "".join(
        f'<a href="{u}" class="{"is-active" if key == active else ""}"'
        f'{" aria-current=\"page\"" if key == active else ""}>{label}</a>'
        for key, u, label in links
    )
    return f'''<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="noto Lab ホーム">
      <img class="brand-logo" src="{prefix}assets/noto-lab-wordmark.png" alt="noto Lab" width="141" height="30">
      <span class="brand-jp">能登研究室</span>
    </a>
    <nav class="desktop-nav" aria-label="主要メニュー">{nav}</nav>
  </div>
</header>'''
