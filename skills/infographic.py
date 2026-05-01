"""
Skill: Infographic Generator — Studio Flow Brand Style
4 templates: numbered, checklist, timeline, comparison
Render bằng Pillow — không phụ thuộc AI image API.
"""
from pathlib import Path
import io

# ── Brand palette ──────────────────────────────────────────────────────────────
BG      = (15,  32,  68)    # Navy chính
ACCENT  = (0,  212, 255)    # Cyan Studio Flow
CARD    = (22,  46,  95)    # Navy nhạt hơn (card bg)
WHITE   = (255, 255, 255)
GRAY    = (180, 200, 230)   # Text phụ
GREEN   = (52,  199,  89)   # Checklist tick
RED_BG  = (180,  40,  40)   # Comparison side B header
CAP_BG  = (0,  180, 220)    # Caption bar

W, H = 1080, 1080
PAD  = 56


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_template(task: str) -> str:
    """Phát hiện loại template từ task string."""
    t = task.lower()
    if any(k in t for k in ["checklist", "check list", "danh sách kiểm tra", "cần làm", "to-do", "todo", "tick"]):
        return "checklist"
    if any(k in t for k in ["timeline", "lộ trình", "quy trình", "các bước", "step by step", "từng bước", "roadmap"]):
        return "timeline"
    if any(k in t for k in ["so sánh", "comparison", " vs ", "versus", "đối chiếu", "ưu nhược", "pros cons"]):
        return "comparison"
    return "numbered"


def render_infographic(task: str, final_text: str, caption: str, index: int = 0) -> bytes | None:
    """
    Tạo infographic JPEG bytes từ task + final_text.
    index: nếu yêu cầu nhiều infographic, index 0,1,2 → section khác nhau.
    """
    try:
        template = detect_template(task)
        title, points = _extract_content(task, final_text, index)

        if template == "checklist":
            return _render_checklist(title, points, caption)
        elif template == "timeline":
            return _render_timeline(title, points, caption)
        elif template == "comparison":
            left_title, left_pts, right_title, right_pts = _extract_comparison(final_text, points)
            return _render_comparison(title, left_title, left_pts, right_title, right_pts, caption)
        else:
            return _render_numbered(title, points, caption)
    except Exception as e:
        import traceback
        print(f"[Infographic] render_infographic thất bại: {e}")
        print(traceback.format_exc())
        return None


# ── Content extraction ─────────────────────────────────────────────────────────

def _extract_content(task: str, final_text: str, index: int = 0):
    """Parse title + bullet points từ markdown final_text."""
    import re
    lines_all = (final_text or "").split("\n")

    # Tìm section thứ (index+1) theo headings
    sec_starts = [i for i, l in enumerate(lines_all) if re.match(r'^#{1,3}\s+', l)]
    si = sec_starts[index] if index < len(sec_starts) else (sec_starts[0] if sec_starts else 0)
    ei = sec_starts[index + 1] if (index + 1) < len(sec_starts) else len(lines_all)
    section = lines_all[si:ei]

    title, points = "", []
    for l in section:
        m = re.match(r'^#{1,3}\s+(.+)', l)
        if m and not title:
            title = m.group(1).strip("# ").strip()
            continue
        m2 = re.match(r'^[-•*]\s+(.+)', l)
        if m2:
            points.append(m2.group(1).strip())
            continue
        m3 = re.match(r'^\d+[.)]\s+(.+)', l)
        if m3:
            points.append(m3.group(1).strip())

    if not title:
        title = task[:80]
    if not points:
        sents = re.split(r'[.!?]\s+', (final_text or "").replace('\n', ' '))
        points = [s.strip() for s in sents if len(s.strip()) > 20][:6]
    if not points:
        points = ["Studio Flow giúp quản lý lịch hẹn hiệu quả",
                  "Hóa đơn tự động, báo cáo tức thì",
                  "Quản lý khách hàng tập trung"]
    return title, points


def _extract_comparison(final_text: str, fallback_points: list):
    """Tách content thành 2 cột cho template comparison."""
    import re
    lines = (final_text or "").split('\n')
    sections, cur = [], {"title": "", "points": []}
    for l in lines:
        m = re.match(r'^#{2,3}\s+(.+)', l)
        if m:
            if cur["points"]:
                sections.append(cur)
            cur = {"title": m.group(1).strip("# ").strip(), "points": []}
        else:
            for pat in [r'^[-•*]\s+(.+)', r'^\d+[.)]\s+(.+)']:
                mm = re.match(pat, l)
                if mm:
                    cur["points"].append(mm.group(1).strip())
                    break
    if cur["points"]:
        sections.append(cur)

    if len(sections) >= 2:
        return (sections[0]["title"] or "Studio Flow",  sections[0]["points"][:4],
                sections[1]["title"] or "Đối thủ / Thủ công", sections[1]["points"][:4])
    else:
        mid = max(1, len(fallback_points) // 2)
        return ("Studio Flow", fallback_points[:mid],
                "Phương pháp cũ", fallback_points[mid:mid+4])


# ── Drawing helpers ────────────────────────────────────────────────────────────

def _font(size, bold=False):
    from skills.brand_assets import _get_font
    return _get_font(size, bold)


def _wrap(draw, text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = (cur + " " + word).strip()
        try:
            tw = draw.textbbox((0, 0), test, font=font)[2]
        except Exception:
            tw = len(test) * 16
        if tw <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text]


def _draw_header(img, draw, title: str, f_title, f_sub) -> int:
    """Vẽ header card. Trả về y sau header."""
    header_h = 148
    draw.rounded_rectangle([(PAD - 10, 28), (W - PAD + 10, 28 + header_h)], radius=14, fill=CARD)
    draw.rectangle([(PAD - 10, 28), (PAD + 5, 28 + header_h)], fill=ACCENT)  # left border
    title_lines = _wrap(draw, title, f_title, W - PAD * 2 - 30)
    ty = 46
    for tl in title_lines[:3]:
        draw.text((PAD + 16, ty), tl, font=f_title, fill=WHITE)
        ty += 50
    draw.text((PAD + 16, ty + 4), "Studio Flow · studioflow.vn", font=f_sub, fill=ACCENT)
    return 28 + header_h + 22


def _draw_caption_bar(draw, caption: str, f_cap):
    cap_h = 60
    draw.rectangle([(0, H - cap_h), (W, H)], fill=CAP_BG)
    try:
        cw = draw.textbbox((0, 0), caption, font=f_cap)[2]
    except Exception:
        cw = len(caption) * 14
    draw.text(((W - cw) // 2, H - cap_h + (cap_h - 28) // 2), caption, font=f_cap, fill=BG)


def _overlay_logo(img):
    """Ghép logo Studio Flow góc dưới phải (trên caption)."""
    from PIL import Image, ImageDraw
    _logo_dir = Path(__file__).parent.parent / "assets" / "logo"
    logo_path = next((p for p in [
        _logo_dir / "Studioflow-logo - BG- removed.png",
        _logo_dir / "Studioflow -Logo.png",
    ] if p.exists()), None)
    if not logo_path:
        return img
    logo = Image.open(str(logo_path)).convert("RGBA")
    lw = 150
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    lx, ly = W - lw - PAD + 10, H - lh - 72
    backing = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(backing)
    try:
        bd.rounded_rectangle([lx - 10, ly - 6, lx + lw + 10, ly + lh + 6], radius=8, fill=(15, 32, 68, 235))
    except AttributeError:
        bd.rectangle([lx - 10, ly - 6, lx + lw + 10, ly + lh + 6], fill=(15, 32, 68, 235))
    base = img.convert("RGBA")
    base = Image.alpha_composite(base, backing)
    base.paste(logo, (lx, ly), mask=logo)
    return base.convert("RGB")


def _finalize(img, draw, caption: str, f_cap) -> bytes:
    """Logo overlay + caption bar → JPEG bytes."""
    img = _overlay_logo(img)
    draw = img.getdraw() if hasattr(img, "getdraw") else None
    from PIL import ImageDraw as _ID
    draw = _ID.Draw(img)
    _draw_caption_bar(draw, caption, f_cap)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=95)
    print(f"[Infographic] OK: {out.tell()} bytes")
    return out.getvalue()


# ── Template: Numbered ─────────────────────────────────────────────────────────

def _render_numbered(title: str, points: list, caption: str) -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 7)], fill=ACCENT)

    f_t = _font(40, bold=True)
    f_p = _font(28)
    f_n = _font(26, bold=True)
    f_c = _font(26)
    f_s = _font(20)

    y = _draw_header(img, draw, title, f_t, f_s)
    max_p = min(len(points), 6)
    avail = H - y - 80
    item_h = min(avail // max(max_p, 1), 130)

    for i, pt in enumerate(points[:max_p]):
        draw.rounded_rectangle([(PAD - 10, y), (W - PAD + 10, y + item_h - 8)], radius=10, fill=CARD)
        cx, cy = PAD + 22, y + item_h // 2 - 4
        r = 21
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=ACCENT)
        ns = str(i + 1)
        try:
            nb = draw.textbbox((0, 0), ns, font=f_n)
            nw, nh = nb[2] - nb[0], nb[3] - nb[1]
        except Exception:
            nw, nh = 16, 24
        draw.text((cx - nw // 2, cy - nh // 2 - 1), ns, font=f_n, fill=BG)
        tx = PAD + 55
        pt_lines = _wrap(draw, pt, f_p, W - tx - PAD - 8)
        pty = y + (item_h - len(pt_lines[:2]) * 34) // 2 - 2
        for pl in pt_lines[:2]:
            draw.text((tx, pty), pl, font=f_p, fill=WHITE)
            pty += 34
        y += item_h

    return _finalize(img, draw, caption, f_c)


# ── Template: Checklist ────────────────────────────────────────────────────────

def _render_checklist(title: str, points: list, caption: str) -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 7)], fill=GREEN)  # green stripe for checklist

    f_t = _font(40, bold=True)
    f_p = _font(28)
    f_c = _font(26)
    f_s = _font(20)

    y = _draw_header(img, draw, title, f_t, f_s)
    max_p = min(len(points), 6)
    avail = H - y - 80
    item_h = min(avail // max(max_p, 1), 130)

    TICK = "✓"
    for i, pt in enumerate(points[:max_p]):
        # Alternating slight shade for readability
        card_color = CARD if i % 2 == 0 else (18, 40, 82)
        draw.rounded_rectangle([(PAD - 10, y), (W - PAD + 10, y + item_h - 8)], radius=10, fill=card_color)
        # Green tick circle
        cx, cy = PAD + 22, y + item_h // 2 - 4
        r = 21
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=GREEN)
        try:
            tb = draw.textbbox((0, 0), TICK, font=f_p)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
        except Exception:
            tw, th = 18, 28
        draw.text((cx - tw // 2, cy - th // 2 - 1), TICK, font=f_p, fill=WHITE)
        # Text
        tx = PAD + 55
        pt_lines = _wrap(draw, pt, f_p, W - tx - PAD - 8)
        pty = y + (item_h - len(pt_lines[:2]) * 34) // 2 - 2
        for pl in pt_lines[:2]:
            draw.text((tx, pty), pl, font=f_p, fill=WHITE)
            pty += 34
        y += item_h

    return _finalize(img, draw, caption, f_c)


# ── Template: Timeline ─────────────────────────────────────────────────────────

def _render_timeline(title: str, points: list, caption: str) -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 7)], fill=ACCENT)

    f_t  = _font(38, bold=True)
    f_pt = _font(26, bold=True)
    f_pd = _font(22)
    f_c  = _font(26)
    f_s  = _font(20)

    y = _draw_header(img, draw, title, f_t, f_s)
    max_p = min(len(points), 6)
    avail = H - y - 80
    step_h = min(avail // max(max_p, 1), 128)

    line_x = PAD + 22  # x của đường dọc timeline

    # Vẽ đường kết nối dọc
    draw.rectangle([(line_x - 3, y + 20), (line_x + 3, y + step_h * max_p - 20)], fill=CARD)

    for i, pt in enumerate(points[:max_p]):
        cy_step = y + step_h // 2
        # Circle trên đường timeline
        r = 22
        draw.ellipse([(line_x - r, cy_step - r), (line_x + r, cy_step + r)], fill=ACCENT)
        ns = str(i + 1)
        try:
            nb = draw.textbbox((0, 0), ns, font=f_pt)
            nw, nh = nb[2] - nb[0], nb[3] - nb[1]
        except Exception:
            nw, nh = 16, 24
        draw.text((line_x - nw // 2, cy_step - nh // 2 - 1), ns, font=f_pt, fill=BG)

        # Content card bên phải
        card_x = line_x + r + 16
        draw.rounded_rectangle([(card_x, y + 6), (W - PAD + 10, y + step_h - 10)], radius=10, fill=CARD)

        # Split point thành title + description nếu có " — " hoặc ": "
        import re as _re
        m = _re.split(r'\s*[—:]\s*', pt, maxsplit=1)
        if len(m) == 2 and len(m[0]) < 40:
            pt_title, pt_desc = m[0], m[1]
        else:
            pt_title, pt_desc = pt, ""

        tx = card_x + 14
        title_lines = _wrap(draw, pt_title, f_pt, W - tx - PAD - 8)
        ty2 = y + 16
        for tl in title_lines[:1]:
            draw.text((tx, ty2), tl, font=f_pt, fill=ACCENT)
            ty2 += 30
        if pt_desc:
            desc_lines = _wrap(draw, pt_desc, f_pd, W - tx - PAD - 8)
            for dl in desc_lines[:2]:
                draw.text((tx, ty2), dl, font=f_pd, fill=GRAY)
                ty2 += 26
        elif len(title_lines) > 1:
            for tl in title_lines[1:3]:
                draw.text((tx, ty2), tl, font=f_pd, fill=GRAY)
                ty2 += 26

        y += step_h

    return _finalize(img, draw, caption, f_c)


# ── Template: Comparison ───────────────────────────────────────────────────────

def _render_comparison(title: str, left_title: str, left_pts: list,
                        right_title: str, right_pts: list, caption: str) -> bytes:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (W, 7)], fill=ACCENT)

    f_t  = _font(36, bold=True)
    f_h  = _font(26, bold=True)
    f_p  = _font(24)
    f_c  = _font(26)
    f_s  = _font(20)

    y = _draw_header(img, draw, title, f_t, f_s)

    col_w = (W - PAD * 2 - 16) // 2
    lx = PAD - 10          # left column x
    rx = lx + col_w + 16   # right column x
    avail = H - y - 80
    max_p = max(len(left_pts), len(right_pts), 1)
    max_p = min(max_p, 5)
    item_h = min((avail - 56) // max_p, 100)

    # Column headers
    draw.rounded_rectangle([(lx, y), (lx + col_w, y + 46)], radius=8, fill=GREEN)
    draw.rounded_rectangle([(rx, y), (rx + col_w, y + 46)], radius=8, fill=RED_BG)
    for header, x, col in [(left_title, lx, col_w), (right_title, rx, col_w)]:
        try:
            hw = draw.textbbox((0, 0), header, font=f_h)[2]
        except Exception:
            hw = len(header) * 14
        draw.text((x + (col - hw) // 2, y + 10), header, font=f_h, fill=WHITE)
    y += 54

    # Divider line
    mid_x = lx + col_w + 8
    draw.rectangle([(mid_x, y), (mid_x + 2, y + item_h * max_p)], fill=CARD)

    # Points
    for i in range(max_p):
        # Left point
        if i < len(left_pts):
            draw.rounded_rectangle([(lx, y + 4), (lx + col_w, y + item_h - 4)], radius=8, fill=CARD)
            draw.ellipse([(lx + 10, y + item_h // 2 - 8), (lx + 26, y + item_h // 2 + 8)], fill=GREEN)
            draw.text((lx + 30, y + (item_h - 34) // 2), "✓", font=f_p, fill=WHITE)
            lpt_lines = _wrap(draw, left_pts[i], f_p, col_w - 46)
            lty = y + (item_h - len(lpt_lines[:2]) * 28) // 2
            for ll in lpt_lines[:2]:
                draw.text((lx + 46, lty), ll, font=f_p, fill=WHITE)
                lty += 28
        # Right point
        if i < len(right_pts):
            draw.rounded_rectangle([(rx, y + 4), (rx + col_w, y + item_h - 4)], radius=8, fill=CARD)
            draw.ellipse([(rx + 10, y + item_h // 2 - 8), (rx + 26, y + item_h // 2 + 8)], fill=RED_BG)
            draw.text((rx + 30, y + (item_h - 34) // 2), "✗", font=f_p, fill=WHITE)
            rpt_lines = _wrap(draw, right_pts[i], f_p, col_w - 46)
            rty = y + (item_h - len(rpt_lines[:2]) * 28) // 2
            for rl in rpt_lines[:2]:
                draw.text((rx + 46, rty), rl, font=f_p, fill=WHITE)
                rty += 28
        y += item_h

    return _finalize(img, draw, caption, f_c)
