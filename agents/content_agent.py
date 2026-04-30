"""
Agent: Content Marketing Agent
Chạy tự động để tạo nội dung marketing hàng ngày/tuần cho Studio Flow
"""
import json
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from skills.content_writing import (
    write_facebook_post,
    write_blog_article,
    write_ad_copy,
    generate_content_calendar,
)
from skills.image_generation import generate_image_sync, IMAGE_PRESETS

_client = get_client()

# generate_image đã bị loại khỏi CONTENT_TOOLS vì Gemini luôn bỏ qua tool call
# và thay bằng mô tả text. Hình ảnh được tạo tự động sau khi agent viết xong content.
CONTENT_TOOLS = [
    {
        "name": "write_facebook_post",
        "description": "Viết bài đăng Facebook cho Studio Flow về một chủ đề cụ thể",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Chủ đề bài viết"},
                "post_type": {
                    "type": "string",
                    "enum": ["educational", "promotional", "testimonial", "tip", "announcement"],
                },
                "include_cta": {"type": "boolean", "default": True},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "write_blog_article",
        "description": "Viết bài blog SEO dài cho website studioflow.vn",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "word_count": {"type": "integer", "default": 800},
            },
            "required": ["title", "keywords"],
        },
    },
    {
        "name": "write_ad_copy",
        "description": "Viết copy cho quảng cáo Facebook/Google/Zalo",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["facebook", "google", "zalo"]},
                "objective": {"type": "string", "enum": ["awareness", "conversion", "retargeting"]},
                "product_feature": {"type": "string"},
            },
            "required": ["platform", "objective", "product_feature"],
        },
    },
    {
        "name": "generate_content_calendar",
        "description": "Tạo lịch nội dung cho cả tháng",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Ví dụ: Tháng 5/2025"},
                "posts_per_week": {"type": "integer", "default": 4},
            },
            "required": ["month"],
        },
    },
]


def _read_img_bytes(local_path: str) -> bytes | None:
    """Đọc ảnh từ local file thành bytes. Trả None nếu thất bại."""
    if not local_path:
        return None
    try:
        from pathlib import Path as _Path
        p = _Path(local_path)
        if p.exists():
            return p.read_bytes()
    except Exception:
        pass
    return None


def _apply_caption_to_bytes(img_bytes: bytes, caption: str) -> bytes:
    """Thêm phụ đề tiếng Việt lên ảnh (bytes in → bytes out), không cần disk."""
    try:
        import io as _io
        import tempfile, os as _os
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(img_bytes)
        tmp.close()
        from skills.brand_assets import add_caption
        add_caption(tmp.name, caption, tmp.name)
        with open(tmp.name, "rb") as f:
            result = f.read()
        _os.unlink(tmp.name)
        print(f"[Caption] Thành công: '{caption[:50]}'")
        return result
    except Exception as e:
        print(f"[Caption failed] {e}")
        return img_bytes  # trả lại ảnh không có caption thay vì crash


def _run_async(coro):
    """Chạy coroutine an toàn dù đang trong event loop hay không."""
    import asyncio
    import concurrent.futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=300)  # 5 phút: Kie AI 150s + Pollinations 90s
    else:
        return asyncio.run(coro)


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Thực thi tool và trả về kết quả."""
    if tool_name == "write_facebook_post":
        return write_facebook_post(**tool_input)
    elif tool_name == "write_blog_article":
        return write_blog_article(**tool_input)
    elif tool_name == "write_ad_copy":
        return write_ad_copy(**tool_input)
    elif tool_name == "generate_content_calendar":
        return generate_content_calendar(**tool_input)
    return f"Tool {tool_name} not implemented"


def run_content_agent(task: str, on_progress=None) -> tuple[str, list]:
    """
    Chạy Content Marketing Agent với agentic loop.
    on_progress(msg): callback để báo tiến trình (dùng trong Streamlit)
    """
    messages = [{"role": "user", "content": task}]

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là Content Marketing Agent của Studio Flow.
Nhiệm vụ: Viết nội dung marketing chất lượng cao. Hình ảnh sẽ được tạo TỰ ĐỘNG bởi hệ thống sau khi bạn viết xong — bạn KHÔNG cần mô tả hay đề xuất hình ảnh.

Quy tắc:
1. Tạo TOÀN BỘ nội dung được yêu cầu (Facebook post, blog, ad copy, v.v.).
2. KHÔNG viết phần "Hình ảnh minh họa", "Mô tả ảnh", "Image suggestion" hay bất kỳ mô tả hình ảnh nào — hệ thống xử lý riêng.
3. Không hỏi lại hay chờ xác nhận giữa chừng.
4. Trình bày kết quả rõ ràng với heading cho từng bài.
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    def _log(msg):
        print(msg)
        if on_progress:
            on_progress(msg)

    _log(f"\n[Content Agent] Bắt đầu task: {task}\n")

    MAX_ITERATIONS = 15
    iteration = 0
    collected_images = []  # track tất cả ảnh đã generate
    # Giữ task gốc riêng để luôn có trong context
    initial_message = messages[0]

    while iteration < MAX_ITERATIONS:
        iteration += 1

        # Trim messages: giữ task gốc + tối đa 6 messages gần nhất
        # (3 cặp assistant/user) để tránh vượt token limit Gemini (1M tokens)
        if len(messages) > 7:
            messages = [initial_message] + messages[-6:]

        response = _client.messages.create(
            model=config.CLAUDE_DEFAULT_MODEL,
            max_tokens=4096,
            system=system,
            tools=CONTENT_TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                _log(f"[Agent]: {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    _log(f"\n[Tool] Đang chạy: {block.name}...")

                    result = _execute_tool(block.name, block.input)
                    _log(f"[Tool] Xong: {str(result)[:120]}")

                    # Giới hạn content mỗi tool result ≤ 2000 ký tự tránh phình token
                    result_str = str(result)
                    if len(result_str) > 2000:
                        result_str = result_str[:1900] + "... [truncated]"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    # Lấy text cuối cùng
    final_text = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            final_text += block.text

    # Xoá mô tả hình ảnh mà Gemini có thể viết trong text (không cần vì hình ảnh tạo tự động)
    import re
    # Pattern 1: "Hình ảnh 1:", "Hình ảnh 2:" (numbered — Gemini hay dùng nhất)
    final_text = re.sub(
        r'\n?\*?\*?Hình\s+ảnh\s+\d+\s*[:\-][^\n]*(?:\n(?!\n)[^\n]*)*',
        '',
        final_text,
        flags=re.IGNORECASE,
    )
    # Pattern 2: Các label khác Gemini có thể dùng
    final_text = re.sub(
        r'\n?\*?\*?(?:Mô tả hình ảnh|Hình ảnh minh họa|Hình ảnh đề xuất|Hình ảnh kèm theo|Image suggestion|Ảnh minh họa|Image:|Ảnh:|🖼️\s*Hình ảnh)[^\n]*(?:\n(?!\n)[^\n]*)*',
        '',
        final_text,
        flags=re.IGNORECASE,
    ).strip()

    # Tạo ảnh tự động — luôn chạy (generate_image đã bị bỏ khỏi tools)
    preset = _pick_preset_for_task(task)
    n = _count_posts(task, final_text)
    aspect_ratio = IMAGE_PRESETS.get(preset, IMAGE_PRESETS["social_post"]).get("aspect_ratio", "1:1")

    # Tạo n prompts + n captions từ nội dung thực tế (1 LLM call)
    _log(f"\n[Image] Đang tạo {n} prompt + phụ đề từ nội dung...")
    image_prompts, image_captions = _make_image_prompts_and_captions(task, final_text, n)
    for idx, (ip, ic) in enumerate(zip(image_prompts, image_captions)):
        _log(f"[Image] Prompt {idx+1}: {ip[:100]}")
        _log(f"[Image] Caption {idx+1}: {ic[:60]}")

    _log(f"[Image] Bắt đầu generate {n} ảnh (aspect={aspect_ratio}, use_reference=False)...")

    for i in range(n):
        try:
            caption = image_captions[i] if i < len(image_captions) else "Studio Flow: Giải pháp quản lý studio số 1 Việt Nam"

            if preset == "infographic":
                # Render infographic bằng Pillow thay vì gọi Kie AI
                _log(f"[Infographic] Đang render infographic {i+1}/{n}...")
                img_bytes = _render_infographic(task, final_text, caption, index=i)
                if img_bytes:
                    collected_images.append((preset, "", "", img_bytes))
                    _log(f"[Infographic] ✓ Infographic {i+1}/{n} hoàn thành ({len(img_bytes)//1024}KB)")
                else:
                    _log(f"[Infographic] ✗ Render thất bại, fallback sang ảnh thường")
                    # Fallback: generate ảnh thường với Kie AI
                    result = generate_image_sync(image_prompts[i], aspect_ratio="1:1", use_reference=False)
                    img_bytes = result.get("img_bytes")
                    if img_bytes:
                        collected_images.append((preset, result.get("local_path",""), result.get("image_url",""), img_bytes))
            else:
                _log(f"[Image] Đang tạo ảnh {i+1}/{n}...")
                result = generate_image_sync(image_prompts[i], aspect_ratio=aspect_ratio, use_reference=False)
                _log(f"[Image] Source: {result.get('source', '?')}")
                local_path = result.get("local_path", "")
                image_url = result.get("image_url", "")
                img_bytes = result.get("img_bytes")

                if caption and img_bytes:
                    img_bytes_with_cap = _apply_caption_to_bytes(img_bytes, caption)
                    if img_bytes_with_cap and len(img_bytes_with_cap) > 1000:
                        img_bytes = img_bytes_with_cap
                        _log(f"[Image] ✓ Phụ đề: {caption[:60]}")
                    else:
                        _log(f"[Image] ✗ Caption thất bại, dùng ảnh không có phụ đề")

                _log(f"[Image] bytes={len(img_bytes) if img_bytes else 0}")
                if img_bytes or local_path or image_url:
                    collected_images.append((preset, local_path, image_url, img_bytes))
                    _log(f"[Image] ✓ Ảnh {i+1}/{n} hoàn thành")
                else:
                    _log(f"[Image] ✗ Ảnh {i+1}: result rỗng")
        except Exception as e:
            import traceback
            _log(f"[Image] ✗ Lỗi {i+1}: {e}")
            _log(traceback.format_exc()[:300])

    # Fallback: nếu Kie AI hoàn toàn thất bại → dùng logo brand asset
    if not collected_images:
        _log("[Image] Fallback: Kie AI không phản hồi, dùng brand asset...")
        try:
            from pathlib import Path as _Path
            _logo_dir = _Path(__file__).parent.parent / "assets" / "logo"
            for _name in ["Studioflow -Logo.png", "Studioflow-logo - BG- removed.png"]:
                _p = _logo_dir / _name
                if _p.exists():
                    collected_images.append(("brand_asset", str(_p), "", _p.read_bytes()))
                    _log(f"[Image] Fallback ✓ dùng {_name}")
                    break
        except Exception as e:
            _log(f"[Image] Fallback ✗: {e}")

    return final_text, collected_images


def _make_image_prompts_and_captions(task: str, final_text: str, n: int) -> tuple[list[str], list[str]]:
    """
    Dùng LLM tạo n image prompts (tiếng Anh) + n captions (tiếng Việt) trong 1 call.
    Trả (prompts_list, captions_list) — mỗi prompt + caption khớp nhau theo index.
    """
    content_snippet = final_text[:800] if final_text else task[:400]
    _fallback_prompts = [
        "Vietnamese photographer stressed looking at overflowing appointment book, messy desk, tired expression, warm office light",
        "Happy couple smiling at professional photography studio reception, bright modern interior, welcoming atmosphere",
        "Studio owner confidently reviewing business analytics on laptop, clean modern office, professional setting",
        "Photography equipment neatly organized in Vietnamese studio, camera lenses on shelf, professional setup",
        "Team of photographers collaborating at photo studio, reviewing images on large screen, creative workspace",
    ]
    _fallback_captions = [
        "Studio Flow: Giải pháp quản lý studio số 1 Việt Nam",
        "Studio Flow: Quản lý lịch hẹn thông minh, không bỏ lỡ khách hàng",
        "Studio Flow: Hóa đơn chuyên nghiệp, báo cáo tự động",
        "Studio Flow Pro: Nâng tầm studio của bạn — 299.000đ/tháng",
        "Studio Flow: Dùng thử miễn phí tại studioflow.vn",
    ]

    try:
        resp = _client.messages.create(
            model=config.CLAUDE_DEFAULT_MODEL,
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": (
                    f"You are creating marketing content for Studio Flow, a Vietnamese photography studio management app.\n\n"
                    f"Task topic: {task[:300]}\n"
                    f"Article content: {content_snippet[:600]}\n\n"
                    f"Create EXACTLY {n} pairs of (image prompt + Vietnamese caption) that DIRECTLY ILLUSTRATE this topic.\n\n"
                    f"FORMAT — return EXACTLY {n*2} lines alternating:\n"
                    f"Line 1: English image prompt (30-50 words, specific realistic scene, Vietnamese people, photography business, emotion + lighting + setting details, NO text/logo in image)\n"
                    f"Line 2: Vietnamese caption (under 15 words, Studio Flow branding, benefit-focused)\n"
                    f"Line 3: English image prompt (completely different scene from Line 1)\n"
                    f"Line 4: Vietnamese caption\n"
                    f"... and so on for {n} pairs.\n\n"
                    f"Rules:\n"
                    f"- Each image must show a DIFFERENT specific scene (not generic studio interior)\n"
                    f"- Scenes must visually represent the topic's key message\n"
                    f"- No numbers, bullets, labels, or explanations — just the lines"
                ),
            }],
        )
        text = ""
        for block in resp.content:
            if hasattr(block, "text") and block.text:
                text = block.text.strip()
                break

        import re as _re
        raw_lines = [
            _re.sub(r'^[\d]+[.)]\s*', '', l.strip()).lstrip("-•* ").strip()
            for l in text.split("\n")
            if l.strip() and len(l.strip()) > 8
        ]

        prompts, captions = [], []
        for idx, line in enumerate(raw_lines):
            if idx % 2 == 0:
                prompts.append(line)
            else:
                captions.append(line)

        # Bổ sung fallback nếu thiếu
        while len(prompts) < n:
            i = len(prompts)
            prompts.append(_fallback_prompts[i % len(_fallback_prompts)])
        while len(captions) < n:
            i = len(captions)
            captions.append(_fallback_captions[i % len(_fallback_captions)])

        return prompts[:n], captions[:n]

    except Exception as e:
        print(f"[Image prompts+captions] LLM thất bại: {e}, dùng fallback")
        return (
            [_fallback_prompts[i % len(_fallback_prompts)] for i in range(n)],
            [_fallback_captions[i % len(_fallback_captions)] for i in range(n)],
        )


# Giữ alias cũ để không break code nếu có chỗ khác gọi
def _make_image_prompts(task: str, final_text: str, n: int) -> list[str]:
    prompts, _ = _make_image_prompts_and_captions(task, final_text, n)
    return prompts


def _pick_preset_for_task(task: str) -> str:
    """Chọn loại output phù hợp dựa trên từ khoá trong task."""
    task_lower = task.lower()
    if any(k in task_lower for k in ["infographic", "infographics", "thống kê", "so sánh", "checklist", "danh sách"]):
        return "infographic"   # Pillow-rendered
    if any(k in task_lower for k in ["banner", "website", "landing", "trang chủ", "hero"]):
        return "hero_banner"   # 16:9
    if any(k in task_lower for k in ["kol", "tiktok", "reels", "story", "dọc"]):
        return "kol_product"   # 9:16
    return "social_post"       # 1:1 default




def _count_posts(task: str, final_text: str) -> int:
    """Đếm số ảnh cần tạo (tối đa 3 để tránh timeout)."""
    import re
    task_lower = task.lower()
    # Ưu tiên: "tạo 3 hình ảnh", "3 ảnh", "3 images"
    m = re.search(r'(\d+)\s*(?:hình\s*ảnh|ảnh|image)', task_lower)
    if m:
        return min(int(m.group(1)), 3)
    # Thứ hai: "3 bài", "2 post" (1 bài = 1 ảnh)
    m = re.search(r'(\d+)\s*(?:bài|post|blog|email|ad)', task_lower)
    if m:
        return min(int(m.group(1)), 3)
    return 1  # mặc định 1 ảnh


def _render_infographic(task: str, final_text: str, caption: str, index: int = 0) -> bytes | None:
    """
    Tạo infographic bằng Pillow — render text + layout trực tiếp.
    Trả JPEG bytes hoặc None nếu thất bại.
    """
    try:
        from PIL import Image, ImageDraw
        import io
        import re
        from pathlib import Path as _Path
        from skills.brand_assets import _get_font

        W, H = 1080, 1080
        PAD = 56

        # Studio Flow brand colors
        BG      = (15, 32, 68)      # Navy
        ACCENT  = (0, 212, 255)     # Cyan
        CARD    = (22, 46, 95)      # Lighter navy
        WHITE   = (255, 255, 255)
        GRAY    = (180, 200, 230)
        CAP_BG  = (0, 180, 220)

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Top accent stripe
        draw.rectangle([(0, 0), (W, 7)], fill=ACCENT)

        # Fonts
        f_title  = _get_font(42, bold=True)
        f_point  = _get_font(28, bold=False)
        f_num    = _get_font(28, bold=True)
        f_cap    = _get_font(26, bold=False)
        f_sub    = _get_font(22, bold=False)

        # --- Parse content ---
        # Extract title: first H1/H2 heading từ final_text
        title = ""
        points = []
        lines_all = final_text.split("\n") if final_text else []

        # Nếu nhiều infographic (index > 0), thử tìm section thứ (index+1)
        section_starts = [i for i, l in enumerate(lines_all) if re.match(r'^#{1,3}\s+', l)]
        start_line = section_starts[index] if index < len(section_starts) else (section_starts[0] if section_starts else 0)
        end_line   = section_starts[index + 1] if (index + 1) < len(section_starts) else len(lines_all)
        section_lines = lines_all[start_line:end_line]

        for l in section_lines:
            m = re.match(r'^#{1,3}\s+(.+)', l)
            if m and not title:
                title = m.group(1).strip()
                continue
            m2 = re.match(r'^[-•*]\s+(.+)', l)
            if m2:
                points.append(m2.group(1).strip())
                continue
            m3 = re.match(r'^\d+[.)]\s+(.+)', l)
            if m3:
                points.append(m3.group(1).strip())

        # Fallback nếu parse thất bại
        if not title:
            title = task[:70]
        if not points:
            # Tách câu từ final_text làm points
            sents = re.split(r'[.!?]\s+', final_text.replace('\n', ' '))
            points = [s.strip() for s in sents if len(s.strip()) > 20][:6]
        if not points:
            points = ["Studio Flow giúp quản lý lịch hẹn thông minh",
                      "Hóa đơn tự động, báo cáo tức thì",
                      "Quản lý khách hàng tập trung, không bỏ sót lead"]

        max_points = min(len(points), 6)

        # --- Vẽ header card ---
        header_h = 140
        draw.rounded_rectangle([(PAD - 10, 30), (W - PAD + 10, 30 + header_h)], radius=14, fill=CARD)
        draw.rectangle([(PAD - 10, 30), (PAD + 4, 30 + header_h)], fill=ACCENT)  # left border

        # Title (word wrap)
        title_lines = _wrap_text_pil(draw, title, f_title, W - PAD * 2 - 20)
        ty = 50
        for tl in title_lines[:3]:
            draw.text((PAD + 10, ty), tl, font=f_title, fill=WHITE)
            ty += 50

        # Subtitle
        draw.text((PAD + 10, ty + 4), f"Studio Flow · studioflow.vn", font=f_sub, fill=ACCENT)

        # --- Vẽ các điểm ---
        y = 30 + header_h + 28
        item_h = int((H - y - 130) / max(max_points, 1))
        item_h = min(item_h, 140)

        for i, point in enumerate(points[:max_points]):
            # Card nền
            draw.rounded_rectangle([(PAD - 10, y), (W - PAD + 10, y + item_h - 10)], radius=10, fill=CARD)

            # Số thứ tự (hình tròn)
            cx, cy_c = PAD + 20, y + item_h // 2 - 5
            r = 22
            draw.ellipse([(cx - r, cy_c - r), (cx + r, cy_c + r)], fill=ACCENT)
            num_str = str(i + 1)
            try:
                nb = draw.textbbox((0, 0), num_str, font=f_num)
                nw, nh = nb[2] - nb[0], nb[3] - nb[1]
            except Exception:
                nw, nh = 18, 28
            draw.text((cx - nw // 2, cy_c - nh // 2 - 1), num_str, font=f_num, fill=BG)

            # Point text (wrap)
            text_x = PAD + 54
            pt_lines = _wrap_text_pil(draw, point, f_point, W - text_x - PAD - 10)
            pt_y = y + (item_h - len(pt_lines[:2]) * 34) // 2 - 5
            for pl in pt_lines[:2]:
                draw.text((text_x, pt_y), pl, font=f_point, fill=WHITE)
                pt_y += 34

            y += item_h

        # --- Logo overlay ---
        _logo_dir = _Path(__file__).parent.parent / "assets" / "logo"
        _candidates = [
            _logo_dir / "Studioflow-logo - BG- removed.png",
            _logo_dir / "Studioflow -Logo.png",
        ]
        logo_path = next((p for p in _candidates if p.exists()), None)
        if logo_path:
            logo = Image.open(str(logo_path)).convert("RGBA")
            logo_w = 160
            logo_h = int(logo.height * logo_w / logo.width)
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            lx = W - logo_w - PAD + 10
            ly = H - logo_h - 68
            backing = Image.new("RGBA", img.size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(backing)
            try:
                bd.rounded_rectangle([lx - 10, ly - 6, lx + logo_w + 10, ly + logo_h + 6], radius=8, fill=(15, 32, 68, 230))
            except AttributeError:
                bd.rectangle([lx - 10, ly - 6, lx + logo_w + 10, ly + logo_h + 6], fill=(15, 32, 68, 230))
            img_rgba = img.convert("RGBA")
            img_rgba = Image.alpha_composite(img_rgba, backing)
            img_rgba.paste(logo, (lx, ly), mask=logo)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)

        # --- Caption bar ---
        cap_h = 60
        draw.rectangle([(0, H - cap_h), (W, H)], fill=CAP_BG)
        try:
            cb = draw.textbbox((0, 0), caption, font=f_cap)
            cw = cb[2] - cb[0]
        except Exception:
            cw = len(caption) * 14
        draw.text(((W - cw) // 2, H - cap_h + (cap_h - 28) // 2), caption, font=f_cap, fill=BG)

        out = io.BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=95)
        print(f"[Infographic] Render OK: {out.tell()} bytes")
        return out.getvalue()

    except Exception as e:
        import traceback
        print(f"[Infographic] Render thất bại: {e}")
        print(traceback.format_exc())
        return None


def _wrap_text_pil(draw, text: str, font, max_width: int) -> list[str]:
    """Ngắt dòng text theo max_width pixel."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        try:
            w = draw.textbbox((0, 0), test, font=font)[2]
        except Exception:
            w = len(test) * 16
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


if __name__ == "__main__":
    result = run_content_agent(
        "Tạo 2 bài Facebook post: 1 bài educational về quản lý lịch hẹn studio, "
        "1 bài promotional về gói Pro 299k. Kèm gợi ý hình ảnh cho mỗi bài."
    )
    print("\n=== KẾT QUẢ ===")
    print(result)
