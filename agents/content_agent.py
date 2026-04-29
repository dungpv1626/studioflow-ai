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

    # Xoá mô tả hình ảnh mà Gemini có thể viết trong text (không cần nữa vì hình ảnh tạo tự động)
    import re
    final_text = re.sub(
        r'\n?\*?\*?(?:Mô tả hình ảnh|Hình ảnh minh họa|Hình ảnh đề xuất|Image suggestion|Ảnh minh họa|Image:|Ảnh:)[^\n]*(?:\n(?!\n)[^\n]*)*',
        '',
        final_text,
        flags=re.IGNORECASE,
    ).strip()

    # Tạo ảnh tự động — luôn chạy (generate_image đã bị bỏ khỏi tools)
    preset = _pick_preset_for_task(task)
    n = _count_posts(task, final_text)
    auto_caption = _make_auto_caption(task)
    _log(f"\n[Image] Bắt đầu tạo {n} ảnh (preset={preset})...")

    for i in range(n):
        try:
            _log(f"[Image] Đang tạo ảnh {i+1}/{n} (preset={preset})...")
            # Dùng generate_image_sync (sync httpx.Client) — tránh asyncio threading issues trên Streamlit Cloud
            p = IMAGE_PRESETS.get(preset, IMAGE_PRESETS["social_post"])
            result = generate_image_sync(p["prompt"], aspect_ratio=p.get("aspect_ratio", "1:1"))
            _log(f"[Image] Source: {result.get('source', '?')}")
            local_path = result.get("local_path", "")
            image_url = result.get("image_url", "")
            img_bytes = result.get("img_bytes")

            if auto_caption and img_bytes:
                img_bytes = _apply_caption_to_bytes(img_bytes, auto_caption)
                _log(f"[Image] Đã thêm phụ đề: {auto_caption[:60]}")

            _log(f"[Image] bytes={len(img_bytes) if img_bytes else 0}")
            if img_bytes or local_path or image_url:
                collected_images.append((preset, local_path, image_url, img_bytes))
                _log(f"[Image] ✓ Ảnh {i+1}/{n} hoàn thành")
            else:
                _log(f"[Image] ✗ Ảnh {i+1}: result rỗng")
        except Exception as e:
            import traceback
            _log(f"[Image] ✗ Lỗi ảnh {i+1}: {e}")
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
