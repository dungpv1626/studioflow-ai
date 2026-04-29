"""
Skill: Image Generation via Kie AI (nano-banana-2)
POST /api/v1/jobs/createTask → poll GET /api/v1/jobs/recordInfo?taskId=...
"""
import httpx
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

KIE_BASE = "https://api.kie.ai"
KIE_API_KEY = os.getenv("KIE_AI_API_KEY", "")

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
    branded_prompt = f"{prompt}, Studio Flow Vietnam photography management app, professional"

    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
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
        "task_id": task_id,
    }

    if image_url:
        # Luôn download về local để overlay logo
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(image_url)
            r.raise_for_status()

        if output_path:
            save_path = str(Path(output_path).resolve())
        else:
            _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            save_path = str(_OUTPUT_DIR / f"gen_{task_id[:8]}.jpg")
        Path(save_path).write_bytes(r.content)

        # Overlay logo nếu có
        try:
            from skills.brand_assets import overlay_logo, get_asset_path
            if get_asset_path("logo_nobg"):
                overlay_logo(save_path, save_path)
        except Exception:
            pass  # Logo chưa upload — bỏ qua, không làm hỏng flow

        result["local_path"] = save_path

    return result


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
        "prompt": "Modern SaaS dashboard on laptop, dark blue theme, Vietnamese wedding photography studio background",
        "aspect_ratio": "16:9",
    },
    "feature_invoice": {
        "prompt": "Clean invoice management UI, Vietnamese dong currency, photography business, minimal design",
        "aspect_ratio": "1:1",
    },
    "feature_calendar": {
        "prompt": "Studio appointment calendar interface, colorful schedule blocks, modern SaaS UI",
        "aspect_ratio": "1:1",
    },
    "kol_product": {
        "prompt": "Vietnamese photographer using mobile app in professional studio, natural lighting, lifestyle photo",
        "aspect_ratio": "9:16",
    },
    "social_post": {
        "prompt": "Dark blue and cyan tech brand logo, photography studio ambiance, modern minimalist",
        "aspect_ratio": "1:1",
    },
    "testimonial_bg": {
        "prompt": "Happy Vietnamese photographer reviewing analytics on tablet, warm studio lighting, professional",
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
