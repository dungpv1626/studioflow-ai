# Studio Flow — AI Marketing & Business Intelligence System

## Tổng quan dự án

Hệ thống AI Agent thay thế phòng Marketing/Truyền thông và Phân tích Kinh doanh cho **Studio Flow** — nền tảng SaaS quản lý studio chụp ảnh tại Việt Nam.

**Founder:** Dũng Phạm  
**Website:** https://studioflow.vn  
**Facebook:** https://web.facebook.com/studioflowtech  
**Zalo:** 0965867228  
**Email:** vietbotaisaas@gmail.com  

**Sản phẩm:** Phần mềm quản lý studio chụp ảnh (Quản lý KH, Lịch hẹn, Hóa đơn, Báo cáo tài chính)  
**Bảng giá:** Free | Pro 299.000đ/tháng | Business 499.000đ/tháng  

---

## Trạng thái dự án (cập nhật 2026-04-29)

### ✅ Đã hoàn thành & hoạt động ổn định

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| **Streamlit Web UI** (`app.py`) | ✅ Production | 6 tabs, auth login, secrets bridge, download button |
| **LLM Backend** (`llm_client.py`) | ✅ Production | Gemini 2.5 Flash, retry 3 lần, fallback gemini-2.5-pro |
| **Streamlit Cloud Deploy** | ✅ Production | GitHub repo `dungpv1626/studioflow-ai`, auto-deploy |
| **Content Agent** (`agents/content_agent.py`) | ✅ Production | Trả tuple `(text, images_list)`, Phase 2 fallback tự tạo ảnh |
| **KOL Agent** (`agents/kol_agent.py`) | ✅ Production | Kịch bản TikTok/Live/YouTube, brief, outreach |
| **Business Analyst Agent** | ✅ Production | Phân tích đối thủ, chiến lược, thị trường |
| **Orchestrator** (`agents/orchestrator.py`) | ✅ Production | Tự phân công task cho agent phù hợp |
| **Kie AI Image Generation** | ✅ Production | Async polling, model `nano-banana-2`, 6 presets, lưu absolute path |
| **Logo Overlay** | ✅ Production | Dùng `logo_primary` (có nền xanh lá), logo_ratio=0.28, luôn hiển thị |
| **Caption tiếng Việt** | ✅ Production | NotoSans tự download, dải xanh Studio Flow phía dưới ảnh |
| **Image bytes in memory** | ✅ Production | Ảnh lưu vào RAM, `st.image(bytes)` không phụ thuộc filesystem |
| **Download button** | ✅ Production | Mỗi ảnh có nút ⬇️ tải về máy |
| **Token overflow fix** | ✅ Production | Trim messages giữ task gốc + 6 messages gần nhất |
| **Brand Assets Manager** | ✅ Production | Tab Brand Assets, preview ảnh, kiểm tra file còn thiếu |
| **Content Writing Skills** | ✅ Production | Facebook post, blog SEO, email, ad copy, content calendar |

### ⚠️ Chưa test đầy đủ / cần kiểm tra thêm

| Hạng mục | Trạng thái | Việc cần làm |
|---|---|---|
| **KOL Agent + Image** | ⚠️ Chưa test | Kiểm tra KOL agent có gọi generate_image không |
| **Orchestrator multi-agent** | ⚠️ Chưa test | Test task phức tạp yêu cầu nhiều agent phối hợp |
| **Web Scraping** (`skills/web_scraping.py`) | ⚠️ Chưa test | Cần kiểm tra Apify token còn hạn không |
| **Caption font trên Cloud** | ⚠️ Chưa confirm | NotoSans tự download lần đầu — cần test internet access trên Streamlit Cloud |
| **Templates & Infographics** | ⚠️ File sai | Thư mục có file hash-name (không dùng được), chưa có template đúng format |

### ❌ Không triển khai (theo quyết định)

| Hạng mục | Lý do |
|---|---|
| **Anthropic Claude API** | User chọn Gemini (miễn phí, có free tier) |
| **Pollinations.AI** | User chọn Kie AI (chất lượng hơn, phù hợp marketing) |
| **Kie AI img2img cho logo** | Logo overlay bằng Pillow đảm bảo logo chính xác 100%, không phụ thuộc AI hallucination |

---

## Kiến trúc hệ thống

```
app.py                           ← Streamlit Web UI (6 tabs + auth + secrets bridge)
├── agents/
│   ├── orchestrator.py          ← AI Marketing Director (MAX_ITERATIONS=10)
│   ├── content_agent.py         ← Tạo nội dung + ảnh, trả (text, images) tuple
│   ├── kol_agent.py             ← Kịch bản & chiến lược KOL (MAX_ITERATIONS=10)
│   └── business_analyst_agent.py ← Phân tích kinh doanh (MAX_ITERATIONS=10)
├── skills/
│   ├── content_writing.py       ← Viết nội dung (Facebook, blog, email, ads)
│   ├── image_generation.py      ← Kie AI + overlay logo, lưu absolute path
│   ├── brand_assets.py          ← overlay_logo(), add_caption(), NotoSans font
│   ├── kol_koc_scripts.py       ← Kịch bản KOL/KOC
│   ├── web_scraping.py          ← Thu thập dữ liệu (Apify)
│   └── market_analysis.py       ← Phân tích thị trường
├── assets/
│   ├── logo/
│   │   ├── Studioflow -Logo.png               ← Logo CHÍNH dùng overlay (nền xanh lá)
│   │   └── Studioflow-logo - BG- removed.png  ← Logo trắng trên nền trong (ít dùng)
│   ├── fonts/                   ← NotoSans tự download vào đây lần đầu
│   ├── templates/               ← Chưa có file đúng format
│   └── infographics/            ← Chưa có file đúng format
├── llm_client.py                ← Gemini adapter (tương thích Anthropic SDK)
├── config.py                    ← Cấu hình & business context
├── output/                      ← Ảnh generate lưu tại đây (gitignored)
├── .env                         ← API keys local (KHÔNG commit)
├── .streamlit/secrets.toml      ← API keys Streamlit Cloud (KHÔNG commit)
└── requirements.txt
```

---

## Khởi chạy

```bash
# Cài dependencies (lần đầu)
pip install -r requirements.txt

# Chạy Web UI
streamlit run app.py

# Test image generation
python test_agent.py
```

---

## API Keys

### Local (`.env`)
```env
GEMINI_API_KEY=...          # LLM chính — Google AI Studio (miễn phí)
KIE_AI_API_KEY=...          # Tạo ảnh — Kie AI nano-banana-2
APIFY_API_TOKEN=...         # Web scraping — Apify
```

### Streamlit Cloud (`.streamlit/secrets.toml` — KHÔNG commit)
```toml
[api_keys]
GEMINI_API_KEY = "..."
KIE_AI_API_KEY = "..."
APIFY_API_TOKEN = "..."

[auth]
password = "studioflow2025"
```

---

## Quyết định kiến trúc quan trọng

### 1. Dùng Gemini thay vì Anthropic Claude API
**Quyết định:** Toàn bộ LLM backend chạy trên Google Gemini 2.5 Flash  
**Lý do:** User không muốn trả phí Anthropic API — Gemini có free tier đủ dùng  
**Cách thực hiện:** `llm_client.py` — wrapper tương thích Anthropic SDK, map model names, convert message formats. Code agents/skills **không cần sửa** ngoài 2 dòng import.  
**Lưu ý:** Model mapping `claude-sonnet-4-6` → `models/gemini-2.5-flash`, fallback `models/gemini-2.5-pro` khi 503.

### 2. Kie AI cho image generation (không dùng Pollinations)
**Quyết định:** Dùng Kie AI `nano-banana-2` model  
**Lý do:** Chất lượng ảnh phù hợp marketing chuyên nghiệp hơn Pollinations  
**Cách thực hiện:** Async polling — POST `/api/v1/jobs/createTask` → poll GET `/api/v1/jobs/recordInfo?taskId=...` mỗi 4 giây, timeout 180 giây  
**Lưu ý quan trọng:** `output_format` KHÔNG được truyền vào payload — API báo lỗi 500 nếu có field này.

### 3. Logo overlay bằng Pillow — dùng logo_primary (có nền)
**Quyết định:** Download ảnh về local, dùng Pillow composite logo lên ảnh. Dùng `logo_primary` (`Studioflow -Logo.png`) thay vì `logo_nobg`.  
**Lý do:** `logo_nobg` có nội dung màu TRẮNG trên nền trong suốt → vô hình trên ảnh sáng màu. `logo_primary` (nền xanh lá gradient) luôn hiển thị rõ trên mọi loại ảnh.  
**Lý do không dùng Kie AI img2img:** Pillow đảm bảo logo chính xác 100%, không bị AI biến thể/hallucinate  
**Cách thực hiện:** `overlay_logo()` — ưu tiên `logo_primary`, logo_ratio=0.28 (28% chiều rộng), góc dưới phải. Nếu chỉ có `logo_nobg` thì tự thêm backing màu xanh Studio Flow phía sau.

### 4. Image bytes lưu trong RAM, không dùng file path
**Quyết định:** Đọc bytes ảnh ngay sau khi generate, lưu trong `collected_images` 4-tuple  
**Lý do:** Path relative gây lỗi trên Streamlit Cloud — CWD khác nhau giữa image_generation.py và app.py. Bytes trong RAM không phụ thuộc filesystem.  
**Cách thực hiện:** `_read_img_bytes(local_path)` trong content_agent.py → `collected_images` lưu `(preset, local_path, image_url, img_bytes)` → app.py dùng `st.image(img_bytes)` và `st.download_button(data=img_bytes)`

### 5. Content Agent trả về `(text, images)` tuple
**Quyết định:** `run_content_agent()` trả `tuple[str, list]` thay vì `str`  
**Lý do:** Gemini không đáng tin cậy trong việc tự include image URL vào final text — thu thập images trực tiếp từ tool results đảm bảo ảnh luôn có  
**Phase 2 fallback:** Nếu Gemini không gọi generate_image trong agentic loop → tự động tạo ảnh dựa trên keyword trong task (không cần LLM)

### 6. Token overflow prevention — trim message history
**Quyết định:** Giữ task gốc + tối đa 6 messages gần nhất, truncate tool result ≤ 2000 ký tự  
**Lý do:** Gemini giới hạn 1,048,576 tokens. Mỗi vòng lặp agent append assistant + tool_results vào messages. Task nhiều bài viết (3-5 posts + ảnh) dễ vượt giới hạn.  
**Áp dụng:** Tất cả 4 agents. Orchestrator và KOL/BA agent còn được đổi từ `while True` → `MAX_ITERATIONS=10`.

### 7. Phụ đề tiếng Việt qua Pillow (không qua Kie AI prompt)
**Quyết định:** Dùng NotoSans font + Pillow ImageDraw để in text tiếng Việt lên ảnh  
**Lý do:** Kie AI không render được tiếng Việt có dấu qua text prompt  
**Cách thực hiện:** `add_caption()` trong `brand_assets.py` — tự download NotoSans-Regular.ttf từ GitHub lần đầu, lưu vào `assets/fonts/`. Vẽ dải nền xanh Studio Flow (#0f2044, opacity 220) phía dưới ảnh, chữ trắng căn giữa.

### 8. Streamlit Community Cloud (không dùng server riêng)
**Quyết định:** Deploy lên Streamlit Cloud miễn phí, kết nối GitHub repo  
**Lý do:** Nhân viên có thể dùng từ bất kỳ máy nào qua browser, không cần setup  
**Cách thực hiện:** GitHub repo private → Streamlit Cloud → secrets qua UI (không commit). `_load_secrets()` trong app.py bridge `st.secrets` → `os.environ` cho các module downstream.

---

## Bước tiếp theo (ưu tiên cao → thấp)

### 🔴 Ưu tiên cao
1. **Upload templates đúng format** vào `assets/templates/` — hiện có file hash-name không dùng được. Cần: `facebook_post.png` (1080×1080), `facebook_story.png` (1080×1920), `hero_banner.png` (1920×600)
2. **Test caption tiếng Việt trên Streamlit Cloud** — NotoSans tự download từ GitHub, cần verify có internet access và không bị timeout
3. **Test KOL Agent + image** — thêm generate_image tool vào KOL Agent (hiện chưa có)

### 🟡 Ưu tiên trung bình
4. **Lưu ảnh lâu dài** — hiện tại ảnh mất khi Streamlit Cloud restart. Cần tích hợp lưu lên Google Drive hoặc Cloudinary để lưu trữ lịch sử
5. **Tích hợp templates vào image pipeline** — overlay nội dung text lên template có sẵn bằng Pillow (thay vì chỉ generate AI + logo)
6. **Kiểm tra web scraping** — chạy thử `find_photography_studios_vietnam("TP.HCM")` với Apify token hiện tại

### 🟢 Ưu tiên thấp (Roadmap)
7. **Social Media Auto-Poster** — tự đăng bài lên Facebook Page theo lịch
8. **Lead Scoring Agent** — chấm điểm lead từ dữ liệu Apify
9. **Customer Support Agent** — trả lời inbox Facebook/Zalo tự động
10. **Competitor Monitor** — alert khi đối thủ thay đổi giá/tính năng

---

## Tính năng theo module

### Content Marketing

| Hàm | File | Output |
|---|---|---|
| `write_facebook_post(topic, post_type)` | `skills/content_writing.py` | String |
| `write_blog_article(title, keywords)` | `skills/content_writing.py` | String |
| `write_email_campaign(type, segment)` | `skills/content_writing.py` | JSON |
| `write_ad_copy(platform, objective)` | `skills/content_writing.py` | JSON |
| `generate_content_calendar(month)` | `skills/content_writing.py` | String |
| `generate_marketing_image(prompt)` | `skills/image_generation.py` | dict với logo |
| `generate_preset_image(preset_key)` | `skills/image_generation.py` | dict với logo |
| `overlay_logo(base, output)` | `skills/brand_assets.py` | path string |
| `add_caption(image, text, output)` | `skills/brand_assets.py` | path string |

### Image Presets (Kie AI)

```python
IMAGE_PRESETS = {
    "hero_banner":      # Banner trang chủ 16:9
    "feature_invoice":  # Tính năng hóa đơn 1:1
    "feature_calendar": # Tính năng lịch hẹn 1:1
    "kol_product":      # KOL cầm điện thoại 9:16
    "social_post":      # Social post 1:1
    "testimonial_bg":   # Background testimonial 16:9
}
```

### KOL/KOC Scripts

| Hàm | Mô tả |
|---|---|
| `generate_tiktok_script(kol, concept, duration)` | Kịch bản TikTok/Reels |
| `generate_facebook_live_script(host, duration)` | Kịch bản Facebook Live |
| `generate_youtube_review_script(reviewer, title)` | Kịch bản YouTube |
| `generate_kol_brief(campaign, tier, platform)` | Brief gửi KOL |
| `generate_kol_outreach_message(name, platform)` | DM tiếp cận KOL |

---

## Lưu ý kỹ thuật quan trọng

- **KHÔNG commit `.env` và `.streamlit/secrets.toml`** — chứa API keys thật
- **Logo file có dấu cách:** `Studioflow -Logo.png` và `Studioflow-logo - BG- removed.png` — không đổi tên
- **Logo_nobg = trắng vô hình:** File BG-removed có logo trắng trên nền trong → vô hình trên ảnh sáng. Luôn dùng `logo_primary` cho overlay.
- **Absolute path cho output:** `_OUTPUT_DIR = Path(__file__).parent.parent / "output"` trong `image_generation.py` — không dùng path relative
- **Asyncio trong Streamlit:** dùng `_run_async()` với `ThreadPoolExecutor` thay vì `asyncio.run()` — tránh conflict event loop
- **Gemini 503:** retry 3 lần với 3s sleep, fallback sang `gemini-2.5-pro`
- **Token limit Gemini:** 1,048,576 tokens — trim messages mỗi iteration, truncate tool results ≤ 2000 ký tự
- **output/ gitignored:** Ảnh generate không commit lên git — mất khi Streamlit Cloud restart
- **NotoSans font:** Tự download từ GitHub khi lần đầu gọi `add_caption()`, lưu tại `assets/fonts/NotoSans-Regular.ttf`

---

*Được xây dựng với Google Gemini API · Kie AI · Apify · Streamlit*  
*Studio Flow © 2024-2026 — Dũng Phạm*
