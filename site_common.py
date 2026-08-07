from __future__ import annotations

import html
from urllib.parse import urlparse


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
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("、。 ,") + "…"


def local_url(url: str, prefix: str = "") -> str:
    if not url or is_external(url) or url.startswith("#") or url.startswith("mailto:"):
        return url
    return prefix + url


def header(profile: dict, prefix: str = "", active: str = "home") -> str:
    links = [
        ("home", f"{prefix}index.html", "Home"),
        ("research", f"{prefix}research/index.html", "Research"),
        ("publications", f"{prefix}works.html", "Publications"),
        ("teaching", f"{prefix}teaching.html", "Teaching"),
        ("profile", f"{prefix}index.html#profile", "Profile"),
        ("contact", f"{prefix}index.html#contact", "Contact"),
    ]
    nav = "".join(
        f'<a href="{u}" class="{"is-active" if key == active else ""}">{label}</a>'
        for key, u, label in links
    )
    mobile = "".join(f'<a href="{u}">{label}</a>' for _, u, label in links)
    return f'''<header class="site-header" id="top">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="noto Lab ホーム">
      <img class="brand-logo" src="{prefix}assets/noto-lab-wordmark.png" alt="noto Lab" width="141" height="30">
    </a>
    <nav class="desktop-nav" aria-label="主要メニュー">{nav}</nav>
    <button class="menu-button" type="button" data-menu-toggle aria-expanded="false" aria-controls="mobile-nav" aria-label="メニューを開く"><span></span><span></span><span></span></button>
  </div>
  <nav class="mobile-nav" id="mobile-nav" data-mobile-nav aria-label="モバイルメニュー">{mobile}</nav>
</header>'''
