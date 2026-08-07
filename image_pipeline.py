from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageOps

THUMB_SMALL_SIZE = (320, 180)
THUMB_LARGE_SIZE = (640, 360)
DETAIL_MAX_SIZE = (1280, 1280)
PROFILE_SIZE = (296, 296)


def _is_external(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def generated_image_paths(category: str, slug: str) -> dict[str, str]:
    base = f"assets/generated/{category}-{slug}"
    return {
        "small": f"{base}-320.webp",
        "large": f"{base}-640.webp",
        "detail": f"{base}-detail.webp",
    }


def _flatten_alpha(im: Image.Image) -> Image.Image:
    if "A" not in im.getbands():
        return im.convert("RGB")
    rgba = im.convert("RGBA")
    bg = Image.new("RGB", rgba.size, "white")
    bg.paste(rgba, mask=rgba.getchannel("A"))
    return bg


def generate_crop_webp(root: Path, dist: Path, source_url: str, output_url: str,
                       size: tuple[int, int], quality: int, contain: bool = False) -> bool:
    if not source_url or _is_external(source_url):
        return False
    source = root / source_url
    if not source.exists() or source.suffix.lower() == ".svg":
        return False
    output = dist / output_url
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source) as raw:
            raw = ImageOps.exif_transpose(raw)
            if contain:
                canvas = Image.new("RGB", size, "white")
                thumb = raw.convert("RGBA") if "A" in raw.getbands() else raw.convert("RGB")
                thumb.thumbnail(size, Image.Resampling.LANCZOS)
                x = (size[0] - thumb.width) // 2
                y = (size[1] - thumb.height) // 2
                if thumb.mode == "RGBA":
                    canvas.paste(thumb, (x, y), thumb)
                else:
                    canvas.paste(thumb, (x, y))
                out = canvas
            else:
                out = ImageOps.fit(
                    _flatten_alpha(raw), size,
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            out.save(output, format="WEBP", quality=quality, method=6, optimize=True)
        return True
    except (OSError, ValueError) as exc:
        print(f"[image] skipped {source_url}: {exc}")
        return False


def generate_detail_webp(root: Path, dist: Path, source_url: str, output_url: str,
                         quality: int = 70) -> bool:
    if not source_url or _is_external(source_url):
        return False
    source = root / source_url
    if not source.exists() or source.suffix.lower() == ".svg":
        return False
    output = dist / output_url
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source) as raw:
            raw = ImageOps.exif_transpose(raw)
            out = _flatten_alpha(raw)
            out.thumbnail(DETAIL_MAX_SIZE, Image.Resampling.LANCZOS)
            out.save(output, format="WEBP", quality=quality, method=6, optimize=True)
        return True
    except (OSError, ValueError) as exc:
        print(f"[image] skipped {source_url}: {exc}")
        return False


def prepare_content_images(root: Path, dist: Path, items: list[dict]) -> None:
    """Create lightweight WebP files for list thumbnails and detail pages."""
    for item in items:
        source = item.get("_thumbnailSource") or item.get("image", "")
        if not source or _is_external(source):
            item["thumbnailSmall"] = source
            item["thumbnailLarge"] = source
            item["detailImage"] = item.get("image", source)
            continue

        paths = generated_image_paths(item["category"], item["slug"])
        contain = bool(item.get("_imageFallback"))
        ok_small = generate_crop_webp(root, dist, source, paths["small"], THUMB_SMALL_SIZE, 42, contain=contain)
        ok_large = generate_crop_webp(root, dist, source, paths["large"], THUMB_LARGE_SIZE, 48, contain=contain)
        detail_source = item.get("image", source)
        ok_detail = generate_detail_webp(root, dist, detail_source, paths["detail"], 70)

        item["thumbnailSmall"] = paths["small"] if ok_small else source
        item["thumbnailLarge"] = paths["large"] if ok_large else item["thumbnailSmall"]
        item["detailImage"] = paths["detail"] if ok_detail else detail_source


def prepare_profile_image(root: Path, dist: Path, data: dict) -> None:
    profile = data.get("profile", {})
    source = profile.get("image", "")
    if not source or _is_external(source):
        return
    output_url = "assets/generated/profile.webp"
    if generate_crop_webp(root, dist, source, output_url, PROFILE_SIZE, 60, contain=False):
        profile["_optimizedImage"] = output_url
