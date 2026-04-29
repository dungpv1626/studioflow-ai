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
        "description": "Tạo hình ảnh marketing sử dụng Kie AI",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Mô tả hình ảnh cần tạo"},
                "preset": {
                    "type": "string",
                    "enum": list(IMAGE_PRESETS.keys()),
                    "description": "Dùng preset có sẵn thay vì prompt",
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
Quy tắc bắt buộc:
1. Với mỗi bài viết (Facebook post, blog, ad copy), LUÔN gọi tool generate_image để tạo hình ảnh phù hợp kèm theo.
2. Ưu tiên dùng preset có sẵn (social_post, hero_banner, feature_invoice, feature_calendar, kol_product, testimonial_bg) nếu phù hợp. Nếu không có preset phù hợp thì dùng custom prompt.
3. Tạo TOÀN BỘ nội dung yêu cầu trong một lần. Không hỏi lại hay chờ xác nhận giữa chừng.
4. Sau khi tạo xong tất cả nội dung và hình ảnh, trình bày kết quả đầy đủ.
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

    while iteration < MAX_ITERATIONS:
        iteration += 1
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
                    # Thu thập image URL
                    if block.name == "generate_image" and "Image URL:" in str(result):
                        url = str(result).replace("Image URL:", "").strip()
                        preset = block.input.get("preset") or "custom"
                        collected_images.append((preset, url))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    # Lấy text cuối cùng
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    # Phase 2: Nếu Gemini không gọi generate_image → tự động tạo ảnh
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
                img_ref = result.get("local_path") or result.get("image_url", "")
                _log(f"[Image] img_ref={img_ref[:80] if img_ref else 'EMPTY'}")
                if img_ref:
                    collected_images.append((preset, img_ref))
                    _log(f"[Image] ✓ Ảnh {i+1} thêm vào collected_images")
                else:
                    _log(f"[Image] ✗ img_ref rỗng, result={result}")
            except Exception as e:
                import traceback
                _log(f"[Image] ✗ Lỗi ảnh {i+1}: {e}")
                _log(traceback.format_exc()[:300])

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
