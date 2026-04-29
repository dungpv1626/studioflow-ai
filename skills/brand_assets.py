"""
Skill: Brand Assets Manager
Quản lý và truy xuất tài nguyên thương hiệu Studio Flow (logo, templates, infographics)
"""
import os
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

ASSET_CATALOG = {
    # Logo
    "logo_primary":      ("logo/Studioflow -Logo.png",              "Logo Studio Flow chính (nền sáng)"),
    "logo_nobg":         ("logo/Studioflow-logo - BG- removed.png", "Logo Studio Flow đã xóa nền (overlay)"),
    "logo_white":        ("logo/logo_white.png",                    "Logo Studio Flow trắng (nền tối)"),
    "logo_icon":         ("logo/logo_icon.png",                     "Icon vuông Studio Flow (avatar/favicon)"),
    "logo_horizontal":   ("logo/logo_horizontal.png",               "Logo nằm ngang"),

    # Templates
    "facebook_post":     ("templates/facebook_post.png",  "Template bài đăng Facebook 1080x1080"),
    "facebook_story":    ("templates/facebook_story.png", "Template Story 1080x1920"),
    "hero_banner":       ("templates/hero_banner.png",    "Banner trang chủ 1920x600"),
    "ad_square":         ("templates/ad_square.png",      "Quảng cáo vuông 1080x1080"),
    "email_header":      ("templates/email_header.png",   "Header email marketing"),

    # Infographics
    "feature_invoice":   ("infographics/feature_invoice.png",  "Infographic tính năng hóa đơn"),
    "feature_calendar":  ("infographics/feature_calendar.png", "Infographic tính năng lịch hẹn"),
    "feature_report":    ("infographics/feature_report.png",   "Infographic tính năng báo cáo"),
    "pricing":           ("infographics/pricing.png",          "Bảng giá 3 gói Free/Pro/Business"),
    "how_it_works":      ("infographics/how_it_works.png",     "Sơ đồ cách hoạt động Studio Flow"),
}


def get_asset_path(key: str) -> Path | None:
    """Trả về đường dẫn tuyệt đối của asset, None nếu không tồn tại."""
    if key not in ASSET_CATALOG:
        return None
    rel_path, _ = ASSET_CATALOG[key]
    full_path = ASSETS_DIR / rel_path
    return full_path if full_path.exists() else None


def list_available_assets() -> dict[str, dict]:
    """Liệt kê tất cả assets có sẵn (đã upload)."""
    available = {}
    for key, (rel_path, description) in ASSET_CATALOG.items():
        full_path = ASSETS_DIR / rel_path
        if full_path.exists():
            size_kb = full_path.stat().st_size // 1024
            available[key] = {
                "path": str(full_path),
                "description": description,
                "size_kb": size_kb,
                "category": rel_path.split("/")[0],
            }
    return available


def list_missing_assets() -> list[str]:
    """Liệt kê assets chưa được upload."""
    missing = []
    for key, (rel_path, description) in ASSET_CATALOG.items():
        full_path = ASSETS_DIR / rel_path
        if not full_path.exists():
            missing.append(f"{key}: {description} → assets/{rel_path}")
    return missing


def get_assets_by_category(category: str) -> dict[str, str]:
    """
    Lấy assets theo category: 'logo', 'templates', 'infographics'
    Returns: {key: path_string} chỉ những file đã tồn tại
    """
    result = {}
    for key, (rel_path, description) in ASSET_CATALOG.items():
        if rel_path.startswith(category + "/"):
            full_path = ASSETS_DIR / rel_path
            if full_path.exists():
                result[key] = str(full_path)
    return result


def pick_asset_for_content(content_type: str) -> str | None:
    """
    Gợi ý asset phù hợp dựa trên loại nội dung.
    Returns: asset key hoặc None nếu không có gợi ý.
    """
    mapping = {
        "facebook_post":    "facebook_post",
        "facebook_story":   "facebook_story",
        "ad":               "ad_square",
        "blog":             "hero_banner",
        "email":            "email_header",
        "invoice":          "feature_invoice",
        "calendar":         "feature_calendar",
        "report":           "feature_report",
        "pricing":          "pricing",
        "tutorial":         "how_it_works",
    }
    for keyword, asset_key in mapping.items():
        if keyword in content_type.lower():
            path = get_asset_path(asset_key)
            if path:
                return asset_key
    return None


def summarize_assets() -> str:
    """Tóm tắt trạng thái assets dùng cho agents."""
    available = list_available_assets()
    missing = list_missing_assets()

    lines = [f"=== Studio Flow Brand Assets ({len(available)}/{len(ASSET_CATALOG)} files) ===\n"]

    for category in ["logo", "templates", "infographics"]:
        cat_assets = {k: v for k, v in available.items() if v["category"] == category}
        if cat_assets:
            lines.append(f"[{category.upper()}]")
            for key, info in cat_assets.items():
                lines.append(f"  ✓ {key}: {info['description']} ({info['size_kb']}KB)")

    if missing:
        lines.append(f"\n[CHƯA UPLOAD — {len(missing)} files]")
        for m in missing:
            lines.append(f"  ✗ {m}")

    return "\n".join(lines)


def overlay_logo(
    base_image_path: str,
    output_path: str,
    position: str = "bottom-right",
    logo_ratio: float = 0.22,
    padding: int = 24,
) -> str:
    """
    Ghép logo Studio Flow (removed background) lên ảnh nền.

    Args:
        base_image_path: Đường dẫn ảnh gốc (đã download về local)
        output_path: Đường dẫn file output
        position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center'
        logo_ratio: Logo chiếm bao nhiêu % chiều rộng ảnh (0.22 = 22%)
        padding: Khoảng cách từ mép ảnh (pixels)
    Returns:
        output_path nếu thành công
    """
    from PIL import Image

    logo_path = get_asset_path("logo_nobg")
    if not logo_path:
        raise FileNotFoundError("Chưa có file logo_nobg. Upload 'Studioflow-logo - BG- removed.png' vào assets/logo/")

    base = Image.open(base_image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo theo tỉ lệ
    logo_w = int(base.width * logo_ratio)
    logo_h = int(logo.height * logo_w / logo.width)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Tính vị trí
    bw, bh = base.size
    lw, lh = logo.size
    positions = {
        "bottom-right": (bw - lw - padding, bh - lh - padding),
        "bottom-left":  (padding, bh - lh - padding),
        "top-right":    (bw - lw - padding, padding),
        "top-left":     (padding, padding),
        "center":       ((bw - lw) // 2, (bh - lh) // 2),
    }
    x, y = positions.get(position, positions["bottom-right"])

    # Composite
    base.paste(logo, (x, y), mask=logo)
    base.convert("RGB").save(output_path, quality=95)
    return output_path


if __name__ == "__main__":
    print(summarize_assets())
