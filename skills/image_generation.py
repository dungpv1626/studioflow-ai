"""
Skill: Image Generation via Kie AI (nano-banana-2)
POST /api/v1/jobs/createTask → poll GET /api/v1/jobs/recordInfo?taskId=...
"""
import httpx
import asyncio
import json
import io
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

KIE_BASE = "https://api.kie.ai"
# KIE_API_KEY đọc lazily trong hàm (không ở module level) để tránh bị capture
# trước khi app.py gọi _load_secrets() bridge Streamlit secrets → os.environ

# Thư mục output dùng absolute path (tránh lỗi relative path trên Streamlit Cloud)
_OUTPUT_DIR = Path(__file__).parent.parent / "output"

ASPECT_MAP = {
    "1:1":   "1:1",
    "16:9":  "16:9",
    "9:16":  "9:16",
    "4:3":   "4:3",
    "3:4":   "3:4",
    "3:2":   "3:2",
    "2:3":   "2:3",
}


async def generate_marketing_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "nano-banana-2",
    output_path: str | None = None,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
) -> dict:
    """
    Tạo hình ảnh marketing qua Kie AI.

    Returns:
        dict: image_url, local_path, prompt_used, task_id
    """
    # KHÔNG thêm tên thương hiệu vào prompt — tránh AI tự vẽ logo sai
    # Logo thật được overlay bằng Pillow sau khi generate
    branded_prompt = f"{prompt}, professional photography studio, Vietnam, high quality"

    # Đọc API key tại thời điểm gọi hàm (sau khi app.py đã bridge secrets vào os.environ)
    kie_api_key = os.getenv("KIE_AI_API_KEY", "")
    if not kie_api_key:
        raise ValueError("KIE_AI_API_KEY chưa được cấu hình. Kiểm tra .env hoặc Streamlit secrets.")

    headers = {
        "Authorization": f"Bearer {kie_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": {
            "prompt": branded_prompt,
            "aspect_ratio": ASPECT_MAP.get(aspect_ratio, "1:1"),
            "resolution": resolution,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Bước 1: Tạo task
        r = await client.post(f"{KIE_BASE}/api/v1/jobs/createTask", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected response (not a dict): {data!r}")

        task_id = (data.get("data") or {}).get("taskId") or data.get("taskId")
        if not task_id:
            raise ValueError(f"Không lấy được taskId: {data}")

        # Bước 2: Poll kết quả (tối đa 3 phút)
        image_url = await _poll_task(client, headers, task_id, max_wait=180)

    result = {
        "image_url": image_url,
        "prompt_used": branded_prompt,
        "local_path": None,
        "img_bytes": None,
        "task_id": task_id,
    }

    if image_url:
        # Download ảnh về memory
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(image_url)
            r.raise_for_status()

        raw_bytes = r.content

        # Overlay logo hoàn toàn trong bộ nhớ (không phụ thuộc disk path)
        img_bytes_with_logo = _overlay_logo_in_memory(raw_bytes)
        result["img_bytes"] = img_bytes_with_logo

        # Vẫn lưu xuống disk để dùng add_caption sau nếu cần
        try:
            if output_path:
                save_path = str(Path(output_path).resolve())
            else:
                _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                save_path = str(_OUTPUT_DIR / f"gen_{task_id[:8]}.jpg")
            Path(save_path).write_bytes(img_bytes_with_logo)
            result["local_path"] = save_path
        except Exception as _save_err:
            print(f"[Image save to disk failed] {_save_err}")

    return result


def _overlay_logo_in_memory(raw_bytes: bytes) -> bytes:
    """Ghép logo Studio Flow lên ảnh hoàn toàn trong bộ nhớ, trả về JPEG bytes."""
    try:
        from PIL import Image, ImageDraw

        # Tìm logo trực tiếp từ đường dẫn tuyệt đối (không import skills.brand_assets
        # để tránh lỗi circular import / sys.path trên Streamlit Cloud)
        _logo_dir = Path(__file__).parent.parent / "assets" / "logo"
        _candidates = [
            _logo_dir / "Studioflow-logo - BG- removed.png",  # logo_nobg ưu tiên
            _logo_dir / "Studioflow -Logo.png",               # logo_primary fallback
        ]
        logo_path = next((p for p in _candidates if p.exists()), None)
        if not logo_path:
            print(f"[Logo overlay] Không tìm thấy logo trong {_logo_dir}: {list(_logo_dir.iterdir()) if _logo_dir.exists() else 'thư mục không tồn tại'}")
            return raw_bytes

        print(f"[Logo overlay] Dùng logo: {logo_path.name}")

        base = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
        logo = Image.open(str(logo_path)).convert("RGBA")

        logo_ratio = 0.28
        padding = 20
        inner_pad = 12

        logo_w = int(base.width * logo_ratio)
        logo_h = int(logo.height * logo_w / logo.width)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        bw, bh = base.size
        lw, lh = logo.size
        x = bw - lw - padding - inner_pad
        y = bh - lh - padding - inner_pad

        # Backing tối màu Studio Flow cho logo trắng
        backing_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(backing_layer)
        bx0, by0 = x - inner_pad, y - inner_pad
        bx1, by1 = x + lw + inner_pad, y + lh + inner_pad
        try:
            bd.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill=(15, 32, 68, 210))
        except AttributeError:
            bd.rectangle([bx0, by0, bx1, by1], fill=(15, 32, 68, 210))
        base = Image.alpha_composite(base, backing_layer)
        base.paste(logo, (x, y), mask=logo)

        out = io.BytesIO()
        base.convert("RGB").save(out, format="JPEG", quality=95)
        print(f"[Logo overlay] Thành công: {len(out.getvalue())} bytes")
        return out.getvalue()

    except Exception as e:
        import traceback
        print(f"[Logo overlay in-memory failed] {e}\n{traceback.format_exc()}")
        return raw_bytes


async def _poll_task(client: httpx.AsyncClient, headers: dict, task_id: str, max_wait: int = 180) -> str:
    """Poll GET /api/v1/jobs/recordInfo cho đến khi xong hoặc timeout."""
    url = f"{KIE_BASE}/api/v1/jobs/recordInfo"
    interval = 4
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval

        r = await client.get(url, headers=headers, params={"taskId": task_id})
        if r.status_code != 200:
            continue

        data = r.json().get("data", {})
        state = data.get("state", "")

        if state == "success":
            result_json = data.get("resultJson", "{}")
            try:
                result_data = json.loads(result_json)
                urls = result_data.get("resultUrls", [])
                if urls:
                    return urls[0]
            except (json.JSONDecodeError, KeyError):
                pass
            raise ValueError(f"Task thành công nhưng không tìm thấy URL trong resultJson: {result_json}")

        if state == "fail":
            raise ValueError(f"Task thất bại: {data.get('failMsg', 'unknown error')}")

    raise TimeoutError(f"Task {task_id} timeout sau {max_wait}s")


# ─── Presets ──────────────────────────────────────────────────────────────────
IMAGE_PRESETS = {
    "hero_banner": {
        "prompt": "Modern SaaS dashboard on laptop, dark blue and cyan theme, Vietnamese wedding photography studio background, no text, no logo",
        "aspect_ratio": "16:9",
    },
    "feature_invoice": {
        "prompt": "Clean invoice management UI mockup, Vietnamese dong currency symbol, photography business, minimal flat design, no brand logo",
        "aspect_ratio": "1:1",
    },
    "feature_calendar": {
        "prompt": "Studio appointment calendar interface mockup, colorful schedule blocks, modern SaaS UI, no text overlay",
        "aspect_ratio": "1:1",
    },
    "kol_product": {
        "prompt": "Vietnamese photographer using mobile app in professional studio, natural lighting, lifestyle photo, no text",
        "aspect_ratio": "9:16",
    },
    "social_post": {
        "prompt": "Professional photography studio interior, dark blue accent lighting, camera equipment, cinematic atmosphere, no text no logo",
        "aspect_ratio": "1:1",
    },
    "testimonial_bg": {
        "prompt": "Happy Vietnamese photographer reviewing analytics on tablet, warm studio lighting, professional portrait, no text",
        "aspect_ratio": "16:9",
    },
}


async def generate_preset_image(preset_key: str, output_path: str | None = None) -> dict:
    """Tạo ảnh từ preset Studio Flow."""
    if preset_key not in IMAGE_PRESETS:
        raise ValueError(f"Preset '{preset_key}' không tồn tại. Chọn: {list(IMAGE_PRESETS.keys())}")
    p = IMAGE_PRESETS[preset_key]
    return await generate_marketing_image(
        p["prompt"],
        aspect_ratio=p.get("aspect_ratio", "1:1"),
        output_path=output_path,
    )


if __name__ == "__main__":
    async def demo():
        result = await generate_preset_image("social_post", output_path="output/test_kie.jpg")
        print(f"Image URL: {result['image_url']}")
        print(f"Task ID:   {result['task_id']}")
        if result["local_path"]:
            print(f"Saved:     {result['local_path']}")
    asyncio.run(demo())
