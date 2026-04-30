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
| **Streamlit Web UI** (`app.py`) | ✅ Production | 7 tabs, auth login, secrets bridge, download button |
| **LLM Backend** (`llm_client.py`) | ✅ Production | Gemini 2.5 Flash, retry 5 lần exponential backoff, fallback gemini-2.5-pro |
| **Streamlit Cloud Deploy** | ✅ Production | GitHub repo `dungpv1626/studioflow-ai`, auto-deploy |
| **Content Agent** (`agents/content_agent.py`) | ✅ Production | Viết content → auto-generate ảnh sync, trả `(text, images_list)` |
| **KOL Agent** (`agents/kol_agent.py`) | ✅ Production | Kịch bản TikTok/Live/YouTube, brief, outreach |
| **Business Analyst Agent** | ✅ Production | Phân tích đối thủ, chiến lược, thị trường |
| **Orchestrator** (`agents/orchestrator.py`) | ✅ Production | Tự phân công task, MAX_ITERATIONS=10 |
| **Monthly Planning Agent** (`agents/planning_agent.py`) | ✅ Production | 7 plan: Content/Marketing/KOL/Ads/PR/Sales/Timeline, tab 7 |
| **Monthly Planning Skills** (`skills/monthly_planning.py`) | ✅ Production | 7 hàm, max_tokens=4096/hàm, 3s sleep giữa các lần gọi |
| **Image Generation — Sync** (`generate_image_sync`) | ✅ Production | httpx.Client sync, Kie AI → Pollinations fallback, không dùng asyncio |
| **Logo Overlay In-Memory** (`_overlay_logo_in_memory`) | ✅ Production | BytesIO, trực tiếp từ file path tuyệt đối, không import brand_assets |
| **Caption tiếng Việt** (`add_caption`) | ✅ Production | NotoSans, temp file approach qua `_apply_caption_to_bytes` |
| **Image bytes in RAM** | ✅ Production | `collected_images` 4-tuple, `st.image(bytes)`, không phụ thuộc filesystem |
| **Download button** | ✅ Production | Mỗi ảnh có nút ⬇️ tải về máy |
| **Token overflow fix** | ✅ Production | Trim messages: task gốc + 6 messages gần nhất, truncate tool results |
| **Brand Assets Manager** | ✅ Production | Tab Brand Assets, preview ảnh, kiểm tra file còn thiếu |
| **Content Writing Skills** | ✅ Production | Facebook post, blog SEO, email, ad copy, content calendar |
| **Retry LLM 503/429** | ✅ Production | 5 attempts: flash ×3 (5/10/20s) → pro ×2 (15s), xử lý 429+500+503 |
| **Tab 5 Image Generation** (`app.py`) | ✅ Production | Chuyển sang `generate_image_sync`, hiển thị `img_bytes` có logo, download button |

### ⚠️ Chưa test đầy đủ / cần kiểm tra thêm

| Hạng mục | Trạng thái | Việc cần làm |
|---|---|---|
| **Image generation trên Cloud** | ⚠️ Chưa xác nhận | Cần user xác nhận ảnh đã hiển thị sau fix generate_image_sync |
| **Caption tiếng Việt trên Cloud** | ⚠️ Chưa confirm | NotoSans tự download từ GitHub — cần verify trên Streamlit Cloud |
| **KOL Agent + Image** | ⚠️ Chưa test | KOL agent chưa tích hợp image generation |
| **Orchestrator multi-agent** | ⚠️ Chưa test | Test task phức tạp yêu cầu nhiều agent phối hợp |
| **Web Scraping** (`skills/web_scraping.py`) | ⚠️ Chưa test | Cần kiểm tra Apify token còn hạn không |
| **Templates & Infographics** | ⚠️ File sai | Thư mục có file hash-name (không dùng được), chưa có template đúng format |
| **Monthly Planner — kết quả đầy đủ** | ⚠️ Cần test lại | Đã fix max_tokens 1500→4096, cần xác nhận 7 sections đầy đủ nội dung |

### ❌ Không triển khai (theo quyết định)

| Hạng mục | Lý do |
|---|---|
| **Anthropic Claude API** | User chọn Gemini (miễn phí, có free tier) |
| **generate_image tool trong Content Agent** | Gemini luôn mô tả ảnh bằng text thay vì gọi tool — loại bỏ, dùng auto-generate sau khi viết xong |
| **asyncio/ThreadPoolExecutor cho image gen** | Gây lỗi silent fail trên Streamlit Cloud — thay bằng httpx.Client sync |
| **Kie AI img2img cho logo** | Pillow overlay đảm bảo logo chính xác 100%, không bị AI hallucinate |

---

## Kiến trúc hệ thống

```
app.py                           ← Streamlit Web UI (7 tabs + auth + secrets bridge)
├── agents/
│   ├── orchestrator.py          ← AI Marketing Director (MAX_ITERATIONS=10)
│   ├── content_agent.py         ← Viết content → auto-generate ảnh sync
│   ├── kol_agent.py             ← Kịch bản & chiến lược KOL (MAX_ITERATIONS=10)
│   ├── business_analyst_agent.py ← Phân tích kinh doanh (MAX_ITERATIONS=10)
│   └── planning_agent.py        ← Monthly Planner, 7 tools, MAX_ITERATIONS=15
├── skills/
│   ├── content_writing.py       ← Viết nội dung (Facebook, blog, email, ads)
│   ├── image_generation.py      ← generate_image_sync (sync), Kie AI + Pollinations
│   ├── brand_assets.py          ← add_caption(), overlay_logo(), NotoSans font
│   ├── monthly_planning.py      ← 7 skill functions, max_tokens=4096 mỗi hàm
│   ├── kol_koc_scripts.py       ← Kịch bản KOL/KOC
│   ├── web_scraping.py          ← Thu thập dữ liệu (Apify)
│   └── market_analysis.py       ← Phân tích thị trường
├── assets/
│   ├── logo/
│   │   ├── Studioflow -Logo.png               ← Logo nền xanh lá (ít dùng)
│   │   └── Studioflow-logo - BG- removed.png  ← Logo trắng + dark backing (DÙNG CHÍNH)
│   ├── fonts/                   ← NotoSans tự download vào đây lần đầu
│   ├── templates/               ← Chưa có file đúng format
│   └── infographics/            ← Chưa có file đúng format
├── llm_client.py                ← Gemini adapter, retry exponential backoff
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

# Test image generation sync
python -c "
from skills.image_generation import generate_image_sync, IMAGE_PRESETS
p = IMAGE_PRESETS['social_post']
r = generate_image_sync(p['prompt'], p.get('aspect_ratio','1:1'))
print(f'source={r[\"source\"]} bytes={len(r[\"img_bytes\"] or b\"\")}')
"
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
**Cách thực hiện:** `llm_client.py` — wrapper tương thích Anthropic SDK, map model names, convert message formats.  
**Lưu ý:** Model mapping `claude-sonnet-4-6` → `models/gemini-2.5-flash`, fallback `models/gemini-2.5-pro` khi 503.

### 2. LLM Retry — Exponential Backoff 5 lần
**Quyết định:** 5 attempts: flash ×3 (chờ 5s/10s/20s) → pro ×2 (15s) → raise  
**Lý do:** Gemini 2.5 Flash bị 503 "high demand" thường xuyên khi planning agent gọi 7 LLM calls liên tiếp. Retry cũ chỉ 3 lần với 3s — quá ngắn.  
**Xử lý:** 503, 429 (rate limit), 500 đều retry. Chỉ raise lỗi khác.

### 3. Image Generation — Sync thay vì Async
**Quyết định:** `generate_image_sync()` dùng `httpx.Client` (blocking), KHÔNG dùng `asyncio`/`ThreadPoolExecutor`  
**Lý do:** `_run_async()` với `ThreadPoolExecutor + asyncio.run(coro)` silently fail trên Streamlit Cloud — event loop của Streamlit can thiệp, exception bị nuốt, img_bytes luôn là None. Confirmed bằng test local: sync hoạt động tốt (329KB JPEG + logo trong < 60s).  
**Chain:** Kie AI sync (150s poll) → Pollinations.AI sync (90s, miễn phí, không cần key) → brand asset logo fallback.

### 4. generate_image bị loại khỏi CONTENT_TOOLS
**Quyết định:** Content Agent không có tool `generate_image` — ảnh được tạo tự động SAU khi agent viết xong  
**Lý do:** Gemini luôn bỏ qua tool call và viết mô tả ảnh bằng text thay thế, bất kể prompt instruction mạnh đến đâu. Giải pháp: để Gemini chỉ làm việc viết content (sở trường), auto-generate ảnh ở bước sau.  
**Regex cleanup:** Strip các pattern "Mô tả hình ảnh", "Hình ảnh minh họa", v.v. khỏi final_text trước khi trả về.

### 5. Logo Overlay — Dùng logo_nobg + Dark Backing
**Quyết định:** Ưu tiên `logo_nobg` (logo trắng trên trong suốt) + vẽ backing hình chữ nhật tối (#0f2044, opacity 210) phía sau  
**Lý do:** `logo_primary` (`Studioflow -Logo.png`) có chữ sự kiện "MSE 2026" — không phải logo brand thực sự. `logo_nobg` là logo thật nhưng màu trắng nên cần backing tối để hiển thị rõ.  
**Cách thực hiện:** `_overlay_logo_in_memory()` — xây path trực tiếp từ `Path(__file__).parent.parent / "assets/logo"` (không import `brand_assets` để tránh circular import/sys.path issues trên Cloud).

### 6. KIE_AI_API_KEY — Đọc Lazy (không ở module level)
**Quyết định:** `os.getenv("KIE_AI_API_KEY")` được gọi BÊN TRONG hàm, không phải ở top-level module  
**Lý do:** Module-level `KIE_API_KEY = os.getenv(...)` chạy tại import time — trước khi `app.py` gọi `_load_secrets()` bridge Streamlit secrets vào `os.environ`. Kết quả: key luôn rỗng trên Cloud, mọi Kie AI call đều 401.

### 7. Monthly Planning Agent — 7 Tools Tuần Tự
**Quyết định:** Planning Agent gọi 7 tools theo thứ tự cố định: Content → Marketing → KOL → Ads → PR → Sales → Master Timeline  
**Lý do:** Master Timeline cần tóm tắt 6 plan trước để tổng hợp. Mỗi tool gọi 1 LLM riêng (max_tokens=4096). Tool results truncate 800 chars để tiết kiệm token agent loop, nhưng `plan_results` dict lưu full content cho output cuối.  
**Sleep:** 3 giây giữa các tool calls để tránh rate limit Gemini khi 7 LLM calls burst liên tiếp.

### 8. Token Overflow Prevention
**Quyết định:** Giữ task gốc + tối đa 6 messages gần nhất; truncate tool results ≤ 2000 ký tự (content agent), ≤ 800 ký tự (planning agent)  
**Lý do:** Gemini giới hạn 1,048,576 tokens. Planning Agent gọi 7 LLM calls × 4096 tokens = ~28k tokens chỉ riêng skill results, chưa kể agent loop messages.  
**Áp dụng:** Tất cả agents. MAX_ITERATIONS: orchestrator/kol/ba=10, content=15, planning=15.

### 9. Pollinations.AI — Fallback Miễn Phí
**Quyết định:** Khi Kie AI fail, dùng `image.pollinations.ai` làm fallback tự động  
**Lý do:** Pollinations miễn phí, không cần API key, chỉ cần GET request. Test local: trả 53KB JPEG trong ~20s. Đảm bảo user luôn nhận được ảnh kể cả khi Kie AI overloaded hoặc hết credits.  
**URL:** `https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&seed={hash}`

### 10. Streamlit Community Cloud
**Quyết định:** Deploy lên Streamlit Cloud miễn phí, kết nối GitHub repo `dungpv1626/studioflow-ai`  
**Lý do:** Nhân viên dùng từ bất kỳ máy nào qua browser, không cần setup môi trường  
**Cách thực hiện:** `_load_secrets()` trong app.py bridge `st.secrets["api_keys"]` → `os.environ` ngay khi app khởi động.

---

## Bước tiếp theo (ưu tiên cao → thấp)

### 🔴 Ưu tiên cao
1. **Xác nhận image generation đã hoạt động trên Cloud** — sau fix `generate_image_sync`, cần user test lại và xác nhận ảnh hiển thị với logo. Nếu vẫn lỗi, kiểm tra log expander để biết source (kie_ai / pollinations / brand_asset).
2. **Xác nhận Monthly Planner đầy đủ nội dung** — sau fix max_tokens 1500→4096, cần test lại plan tháng 5/2026 để xác nhận 7 sections có nội dung chi tiết (không bị cắt giữa chừng).
3. **Upload templates đúng format** — `assets/templates/` cần: `facebook_post.png` (1080×1080), `facebook_story.png` (1080×1920), `hero_banner.png` (1920×600).

### 🟡 Ưu tiên trung bình
4. **Test caption tiếng Việt trên Streamlit Cloud** — NotoSans tự download từ GitHub lần đầu, cần verify không bị timeout hoặc lỗi network trên Cloud.
5. **Tích hợp image generation vào KOL Agent** — hiện KOL agent chưa tạo ảnh kèm theo kịch bản.
6. **Lưu ảnh lâu dài** — ảnh mất khi Streamlit Cloud restart. Xem xét Google Drive hoặc Cloudinary.
7. **Kiểm tra web scraping** — chạy thử `find_photography_studios_vietnam("TP.HCM")` với Apify token hiện tại.

### 🟢 Ưu tiên thấp (Roadmap)
8. **Social Media Auto-Poster** — tự đăng bài lên Facebook Page theo lịch
9. **Lead Scoring Agent** — chấm điểm lead từ dữ liệu Apify
10. **Customer Support Agent** — trả lời inbox Facebook/Zalo tự động
11. **Competitor Monitor** — alert khi đối thủ thay đổi giá/tính năng

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
| `generate_image_sync(prompt, aspect_ratio)` | `skills/image_generation.py` | dict: img_bytes+logo |
| `generate_marketing_image(prompt)` | `skills/image_generation.py` | dict async (dùng cho Image tab) |
| `generate_preset_image(preset_key)` | `skills/image_generation.py` | dict async (dùng cho Image tab) |
| `_overlay_logo_in_memory(raw_bytes)` | `skills/image_generation.py` | bytes với logo |
| `add_caption(image, text, output)` | `skills/brand_assets.py` | path string |
| `_apply_caption_to_bytes(bytes, caption)` | `agents/content_agent.py` | bytes với caption |

### Image Presets (6 presets)

```python
IMAGE_PRESETS = {
    "hero_banner":      "16:9 — Banner trang chủ",
    "feature_invoice":  "1:1  — Tính năng hóa đơn",
    "feature_calendar": "1:1  — Tính năng lịch hẹn",
    "kol_product":      "9:16 — KOL cầm điện thoại",
    "social_post":      "1:1  — Social post (default)",
    "testimonial_bg":   "16:9 — Background testimonial",
}
```

### Monthly Planning (7 plans)

| Tool | Skill | Output |
|---|---|---|
| `create_content_posting_plan` | `monthly_planning.py` | Lịch đăng bài chi tiết từng ngày |
| `create_marketing_campaign_plan` | `monthly_planning.py` | Campaigns, KPIs, phân bổ ngân sách |
| `create_kol_plan` | `monthly_planning.py` | Profile KOL, brief, timeline tiếp cận |
| `create_paid_ads_plan` | `monthly_planning.py` | Facebook/Zalo Ads, targeting, A/B test |
| `create_pr_communications_plan` | `monthly_planning.py` | Seeding, community, báo chí |
| `create_sales_business_plan` | `monthly_planning.py` | Lead pipeline, outreach script |
| `create_master_timeline` | `monthly_planning.py` | Bảng tổng hợp theo tuần + KPIs |

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
- **KHÔNG dùng `asyncio` cho image generation trong content_agent** — dùng `generate_image_sync()` (httpx.Client sync). Lỗi root cause đã được xác nhận: ThreadPoolExecutor silently fail trên Streamlit Cloud.
- **KIE_AI_API_KEY phải đọc lazy** — `os.getenv(...)` bên trong hàm, không phải module level. Module level capture trước khi `_load_secrets()` chạy → key rỗng.
- **Logo path xây trực tiếp** — `Path(__file__).parent.parent / "assets/logo"` trong `image_generation.py`, không import `skills.brand_assets` (tránh circular import trên Cloud).
- **Gemini 503:** retry 5 lần exponential backoff (5/10/20/15/0s), xử lý 429+500+503
- **Token limit Gemini:** 1,048,576 tokens — trim messages mỗi iteration, truncate tool results
- **output/ gitignored:** Ảnh generate không commit lên git — mất khi Streamlit Cloud restart
- **NotoSans font:** Tự download từ GitHub khi lần đầu gọi `add_caption()`, lưu tại `assets/fonts/NotoSans-Regular.ttf`
- **Planning Agent tool result:** Truncate 800 chars (đủ để agent biết xong), full content lưu trong `plan_results` dict để build output cuối

---

*Được xây dựng với Google Gemini API · Kie AI · Pollinations.AI · Apify · Streamlit*  
*Studio Flow © 2024-2026 — Dũng Phạm*
