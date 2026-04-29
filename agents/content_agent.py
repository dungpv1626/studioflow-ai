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
from skills.image_generation import generate_marketing_image, generate_preset_image, IMAGE_PRESETS

_client = get_client()

# Tools định nghĩa cho agent
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
        "name": "generate_image",
        "description": "Tạo hình ảnh marketing sử dụng Kie AI. Có thể thêm phụ đề tiếng Việt trực tiếp lên ảnh.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Mô tả hình ảnh cần tạo"},
                "preset": {
                    "type": "string",
                    "enum": list(IMAGE_PRESETS.keys()),
                    "description": "Dùng preset có sẵn thay vì prompt",
                },
                "caption": {
                    "type": "string",
                    "description": "Phụ đề tiếng Việt sẽ được in trực tiếp lên ảnh (dải chữ phía dưới)",
                },
            },
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
            return future.result(timeout=120)
    else:
        return asyncio.run(coro)


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Thực thi tool và trả về kết quả."""
    if tool_name == "write_facebook_post":
        return write_facebook_post(**tool_input)
    elif tool_name == "write_blog_article":
        return write_blog_article(**tool_input)
    elif tool_name == "generate_image":
        try:
            if "preset" in tool_input:
                from skills.image_generation import generate_preset_image
                result = _run_async(generate_preset_image(tool_input["preset"]))
            else:
                result = _run_async(generate_marketing_image(tool_input["prompt"]))
            # Ưu tiên local_path (đã có logo), fallback sang image_url
            img_ref = result.get("local_path") or result.get("image_url", "")
            return f"Image URL: {img_ref}"
        except Exception as e:
            return f"[Image generation failed: {e}]"
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

QUY TẮC BẮT BUỘC — KHÔNG ĐƯỢC VI PHẠM:
1. SAU KHI viết xong mỗi bài viết, PHẢI gọi tool generate_image ngay lập tức.
2. TUYỆT ĐỐI KHÔNG mô tả hình ảnh bằng text (không viết "Hình ảnh minh họa:", "Image:", "Ảnh đề xuất:", v.v.). Hệ thống sẽ tự tạo ảnh qua tool.
3. Chọn preset phù hợp: social_post (mặc định), feature_invoice (hóa đơn), feature_calendar (lịch hẹn), kol_product (KOL/video), hero_banner (banner), testimonial_bg (đánh giá).
4. LUÔN truyền "caption" — phụ đề tiếng Việt ngắn, in lên ảnh. VD: caption="Studio Flow: Quản lý studio thông minh!"
5. Tạo TOÀN BỘ nội dung trong một lần. Không hỏi lại giữa chừng.
6. Sau khi tạo xong toàn bộ nội dung và hình ảnh, tổng kết ngắn.

Thứ tự làm việc đúng:
→ Viết nội dung bài 1 → Gọi generate_image cho bài 1 → Viết nội dung bài 2 → Gọi generate_image cho bài 2 → ...
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

                    # Xử lý generate_image riêng để lấy img_bytes trực tiếp từ memory
                    if block.name == "generate_image":
                        try:
                            if "preset" in block.input:
                                img_result = _run_async(generate_preset_image(block.input["preset"]))
                            else:
                                img_result = _run_async(generate_marketing_image(block.input["prompt"]))
                            local_path = img_result.get("local_path", "")
                            image_url = img_result.get("image_url", "")
                            # img_bytes đã được overlay logo trong memory bởi image_generation.py
                            img_bytes = img_result.get("img_bytes")

                            # Thêm phụ đề tiếng Việt nếu có
                            caption = block.input.get("caption", "").strip()
                            if caption and img_bytes:
                                img_bytes = _apply_caption_to_bytes(img_bytes, caption)
                                _log(f"[Tool] Đã thêm phụ đề: {caption[:60]}")

                            preset_name = block.input.get("preset") or "custom"
                            if img_bytes or local_path or image_url:
                                collected_images.append((preset_name, local_path, image_url, img_bytes))
                                _log(f"[Tool] Xong: bytes={len(img_bytes) if img_bytes else 0} local={local_path[:60] if local_path else 'none'}")
                            result = f"Ảnh đã được tạo thành công (có logo Studio Flow)"
                        except Exception as e:
                            import traceback
                            result = f"[Image generation failed: {e}]"
                            _log(f"[Tool] Lỗi generate_image: {e}")
                    else:
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

    # Phase 2: Nếu Gemini không gọi generate_image → tự động tạo ảnh qua Kie AI
    _log(f"\n[Debug] collected_images={len(collected_images)}, final_text_len={len(final_text)}")
    if not collected_images and final_text.strip():
        preset = _pick_preset_for_task(task)
        n = _count_posts(task, final_text)
        _log(f"[Image] Phase 2 bắt đầu: preset={preset}, n={n}")
        for i in range(n):
            try:
                _log(f"[Image] Đang tạo ảnh {i+1}/{n}...")
                result = _run_async(generate_preset_image(preset))
                _log(f"[Image] Kết quả raw: {str(result)[:200]}")
                local_path = result.get("local_path", "")
                image_url = result.get("image_url", "")
                # img_bytes đã có logo từ image_generation.py
                img_bytes = result.get("img_bytes")

                # Phase 2: thêm phụ đề tự động
                auto_caption = _make_auto_caption(task)
                if auto_caption and img_bytes:
                    img_bytes = _apply_caption_to_bytes(img_bytes, auto_caption)
                    _log(f"[Image] Đã thêm phụ đề: {auto_caption[:60]}")

                _log(f"[Image] bytes={len(img_bytes) if img_bytes else 0} local={local_path[:60] if local_path else 'EMPTY'}")
                if img_bytes or local_path or image_url:
                    collected_images.append((preset, local_path, image_url, img_bytes))
                    _log(f"[Image] ✓ Ảnh {i+1} thêm vào collected_images")
                else:
                    _log(f"[Image] ✗ Không có gì, result={result}")
            except Exception as e:
                import traceback
                _log(f"[Image] ✗ Lỗi ảnh {i+1}: {e}")
                _log(traceback.format_exc()[:300])

    # Phase 3: Nếu Kie AI cũng thất bại → dùng brand asset local làm fallback
    if not collected_images:
        _log("[Image] Phase 3: Kie AI không hoạt động, dùng brand asset local...")
        try:
            from skills.brand_assets import get_asset_path
            from pathlib import Path as _Path
            logo_path = get_asset_path("logo_primary") or get_asset_path("logo_nobg")
            if logo_path and _Path(logo_path).exists():
                img_bytes = _Path(logo_path).read_bytes()
                collected_images.append(("brand_asset", str(logo_path), "", img_bytes))
                _log(f"[Image] Phase 3 ✓ dùng {logo_path.name}")
        except Exception as e:
            _log(f"[Image] Phase 3 ✗: {e}")

    return final_text, collected_images


def _pick_preset_for_task(task: str) -> str:
    """Chọn preset ảnh phù hợp dựa trên từ khoá trong task."""
    task_lower = task.lower()
    if any(k in task_lower for k in ["hóa đơn", "invoice", "thanh toán"]):
        return "feature_invoice"
    if any(k in task_lower for k in ["lịch hẹn", "calendar", "lịch", "appointment"]):
        return "feature_calendar"
    if any(k in task_lower for k in ["kol", "tiktok", "reels", "video"]):
        return "kol_product"
    if any(k in task_lower for k in ["testimonial", "review", "đánh giá"]):
        return "testimonial_bg"
    if any(k in task_lower for k in ["banner", "website", "landing", "trang chủ"]):
        return "hero_banner"
    return "social_post"  # default


def _make_auto_caption(task: str) -> str:
    """Tạo phụ đề tự động từ task cho Phase 2 fallback."""
    task_lower = task.lower()
    if any(k in task_lower for k in ["hóa đơn", "invoice"]):
        return "Studio Flow: Hóa đơn chuyên nghiệp, quản lý thu chi dễ dàng!"
    if any(k in task_lower for k in ["lịch hẹn", "calendar", "lịch"]):
        return "Studio Flow: Quản lý lịch hẹn thông minh — không bỏ lỡ khách hàng nào!"
    if any(k in task_lower for k in ["kol", "tiktok", "reels"]):
        return "Studio Flow: Nền tảng quản lý studio hàng đầu Việt Nam"
    if any(k in task_lower for k in ["pro", "299", "gói"]):
        return "Studio Flow Pro — Chỉ 299.000đ/tháng, nâng tầm studio của bạn!"
    if any(k in task_lower for k in ["free", "miễn phí"]):
        return "Studio Flow: Dùng miễn phí, nâng cấp khi cần — không ràng buộc!"
    return "Studio Flow: Giải pháp quản lý studio chụp ảnh số 1 Việt Nam"


def _count_posts(task: str, final_text: str) -> int:
    """Đếm số bài viết cần tạo ảnh (tối đa 5)."""
    import re
    # Tìm số trong task: "3 bài", "2 post", "viết 4"
    m = re.search(r'(\d+)\s*(bài|post|blog|email|ad)', task.lower())
    if m:
        return min(int(m.group(1)), 5)
    # Đếm số lần xuất hiện heading bài viết trong kết quả
    headings = len(re.findall(r'(?:bài\s*\d+|##\s*bài|post\s*\d+)', final_text.lower()))
    if headings > 0:
        return min(headings, 5)
    return 1  # mặc định 1 ảnh


if __name__ == "__main__":
    result = run_content_agent(
        "Tạo 2 bài Facebook post: 1 bài educational về quản lý lịch hẹn studio, "
        "1 bài promotional về gói Pro 299k. Kèm gợi ý hình ảnh cho mỗi bài."
    )
    print("\n=== KẾT QUẢ ===")
    print(result)
