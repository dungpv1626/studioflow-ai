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

### ✅ Đã hoàn thành

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| **Streamlit Web UI** (`app.py`) | ✅ Hoạt động | 6 tabs: Orchestrator, Content, KOL, Business Analyst, Image, Brand Assets |
| **LLM Backend** (`llm_client.py`) | ✅ Hoạt động | Gemini 2.5 Flash qua OpenAI-compatible endpoint, retry + fallback |
| **Content Agent** (`agents/content_agent.py`) | ✅ Hoạt động | Tạo bài viết + ảnh trong cùng 1 lần chạy, progress callback realtime |
| **KOL Agent** (`agents/kol_agent.py`) | ✅ Hoạt động | Kịch bản TikTok/Live/YouTube, brief, outreach |
| **Business Analyst Agent** | ✅ Hoạt động | Phân tích đối thủ, chiến lược, thị trường |
| **Orchestrator** (`agents/orchestrator.py`) | ✅ Hoạt động | Tự phân công task cho agent phù hợp |
| **Kie AI Image Generation** | ✅ Hoạt động | Async polling, model `nano-banana-2`, 6 presets |
| **Logo Overlay** (`skills/brand_assets.py`) | ✅ Hoạt động | Tự động ghép logo removed-background vào góc dưới phải ảnh |
| **Brand Assets Manager** | ✅ Hoạt động | Tab Brand Assets, preview ảnh, kiểm tra file còn thiếu |
| **Content Writing Skills** | ✅ Hoạt động | Facebook post, blog SEO, email, ad copy, content calendar |

### ⚠️ Chưa test đầy đủ / cần kiểm tra thêm

| Hạng mục | Trạng thái | Việc cần làm |
|---|---|---|
| **KOL Agent + Image** | ⚠️ Chưa test | Kiểm tra KOL agent có gọi generate_image không |
| **Orchestrator multi-agent** | ⚠️ Chưa test | Test task phức tạp yêu cầu nhiều agent phối hợp |
| **Web Scraping** (`skills/web_scraping.py`) | ⚠️ Chưa test | Cần kiểm tra Apify token còn hạn không |
| **Brand Assets đầy đủ** | ⚠️ Chỉ có logo | Còn thiếu templates và infographics |

### ❌ Không triển khai (theo quyết định)

| Hạng mục | Lý do |
|---|---|
| **Anthropic API** | User chọn Gemini (miễn phí, có free tier) |
| **Pollinations.AI** | User chọn Kie AI (chất lượng hơn, phù hợp marketing) |

---

## Kiến trúc hệ thống

```
app.py                           ← Streamlit Web UI (6 tabs)
├── agents/
│   ├── orchestrator.py          ← AI Marketing Director
│   ├── content_agent.py         ← Tạo nội dung + ảnh (có logo)
│   ├── kol_agent.py             ← Kịch bản & chiến lược KOL
│   └── business_analyst_agent.py ← Phân tích kinh doanh
├── skills/
│   ├── content_writing.py       ← Viết nội dung (Facebook, blog, email, ads)
│   ├── image_generation.py      ← Kie AI + tự động overlay logo
│   ├── brand_assets.py          ← Quản lý logo/template/infographic
│   ├── kol_koc_scripts.py       ← Kịch bản KOL/KOC
│   ├── web_scraping.py          ← Thu thập dữ liệu (Apify)
│   └── market_analysis.py       ← Phân tích thị trường
├── assets/
│   ├── logo/
│   │   ├── Studioflow -Logo.png
│   │   └── Studioflow-logo - BG- removed.png   ← Dùng để overlay
│   ├── templates/               ← Chưa có file
│   └── infographics/            ← Chưa có file
├── llm_client.py                ← Gemini adapter (tương thích Anthropic SDK)
├── config.py                    ← Cấu hình & business context
├── output/                      ← Ảnh generate lưu tại đây
├── .env                         ← API keys (KHÔNG commit)
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

## API Keys (.env)

```env
GEMINI_API_KEY=...          # LLM chính — Google AI Studio (miễn phí)
KIE_AI_API_KEY=...          # Tạo ảnh — Kie AI nano-banana-2
APIFY_API_TOKEN=...         # Web scraping — Apify
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
**Lưu ý quan trọng:** `output_format` không được truyền vào payload — API báo lỗi 500 nếu có field này.

### 3. Logo overlay bằng Pillow (không dùng Kie AI img2img)
**Quyết định:** Download ảnh về local, dùng Pillow composite logo lên ảnh  
**Lý do:** Đơn giản, không tốn API call thêm, logo luôn đúng 100% thương hiệu  
**Cách thực hiện:** `skills/brand_assets.py::overlay_logo()` — dùng `logo_nobg` (removed background), paste vào góc dưới phải, logo chiếm 22% chiều rộng ảnh  
**File logo:** `assets/logo/Studioflow-logo - BG- removed.png`

### 4. Content Agent trả về `(text, images)` tuple
**Quyết định:** `run_content_agent()` trả `tuple[str, list]` thay vì `str`  
**Lý do:** Gemini không đáng tin cậy trong việc tự include image URL vào final text — thu thập URL trực tiếp từ tool results đảm bảo ảnh luôn xuất hiện  
**Cách thực hiện:** `collected_images: list[(preset, path)]` track trong vòng lặp, app.py render bằng `st.image()` thay vì markdown

### 5. Streamlit Web UI thay vì CLI
**Quyết định:** Giao diện web thay vì chạy Python script  
**Lý do:** User cần giao diện dễ dùng, không cần biết code  
**Cách thực hiện:** `app.py` — 6 tabs, progress callback realtime, download kết quả, preview ảnh

---

## Bước tiếp theo (ưu tiên cao → thấp)

### 🔴 Ưu tiên cao
1. **Upload templates và infographics** vào `assets/templates/` và `assets/infographics/` — hiện chỉ có logo
2. **Test KOL Agent + image** — kiểm tra kịch bản TikTok có kèm ảnh generated không
3. **Test Orchestrator** với task phức tạp (ví dụ: "Chuẩn bị content tuần này + brief KOL")

### 🟡 Ưu tiên trung bình
4. **Tích hợp templates vào image pipeline** — thay vì chỉ overlay logo, có thể overlay nội dung text lên template có sẵn bằng Pillow
5. **Thêm image vào KOL Agent** — tương tự Content Agent, KOL Agent cũng nên generate ảnh kèm kịch bản
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
| `generate_marketing_image(prompt)` | `skills/image_generation.py` | dict (có logo) |
| `generate_preset_image(preset_key)` | `skills/image_generation.py` | dict (có logo) |
| `overlay_logo(base, output)` | `skills/brand_assets.py` | path string |

### Image Presets (Kie AI)

```python
IMAGE_PRESETS = {
    "hero_banner"      # Banner trang chủ 16:9
    "feature_invoice"  # Tính năng hóa đơn 1:1
    "feature_calendar" # Tính năng lịch hẹn 1:1
    "kol_product"      # KOL cầm điện thoại 9:16
    "social_post"      # Social post 1:1
    "testimonial_bg"   # Background testimonial 16:9
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

## Lưu ý kỹ thuật

- **KHÔNG commit `.env`** — chứa API keys thật
- **Asyncio trong Streamlit**: dùng `_run_async()` trong `content_agent.py` thay vì `asyncio.run()` trực tiếp — tránh conflict event loop
- **Agentic loop**: giới hạn `MAX_ITERATIONS = 15` để tránh vòng lặp vô tận
- **Gemini 503**: retry 3 lần với 3s sleep, fallback sang `gemini-2.5-pro`
- **Ảnh output**: lưu tại `output/gen_<taskId[:8]>.jpg`, đã có logo overlay
- **Logo file names có dấu cách**: `Studioflow -Logo.png` và `Studioflow-logo - BG- removed.png` — không đổi tên để khớp với `brand_assets.py`

---

*Được xây dựng với Google Gemini API · Kie AI · Apify · Streamlit*  
*Studio Flow © 2024-2026 — Dũng Phạm*
