"""
Skill: Monthly Planning
Tạo bộ kế hoạch hoạt động tháng cho team kinh doanh, marketing, truyền thông Studio Flow.
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT

_client = get_client()

CACHED_SYSTEM = [
    {
        "type": "text",
        "text": STUDIOFLOW_CONTEXT + "\nBạn là chuyên gia lập kế hoạch marketing và kinh doanh cho Studio Flow. Viết bằng tiếng Việt, cụ thể, actionable, phù hợp thực tế startup SaaS Việt Nam.",
        "cache_control": {"type": "ephemeral"},
    }
]


def create_content_posting_plan(month: str, posts_per_week: int = 5, focus_theme: str = "") -> str:
    """Lịch đăng bài chi tiết: ngày, kênh, loại bài, chủ đề, caption ngắn, hashtag."""
    theme_note = f"\nChủ đề trọng tâm tháng này: {focus_theme}" if focus_theme else ""
    prompt = f"""Tạo LỊCH ĐĂNG BÀI CHI TIẾT cho Studio Flow {month}.
Số bài/tuần: {posts_per_week}{theme_note}

Yêu cầu output:
1. Bảng lịch đăng bài theo tuần (Tuần 1 → Tuần 4/5), mỗi bài gồm:
   - Ngày đăng | Kênh (Facebook/Zalo/TikTok) | Loại bài | Chủ đề cụ thể | Caption ngắn 1-2 câu | Hashtag gợi ý

2. Phân bổ loại bài:
   - 35% Educational (tips quản lý studio, kiến thức ngành)
   - 25% Product feature (tính năng nổi bật Studio Flow)
   - 20% Social proof (testimonial, case study khách hàng)
   - 20% Promotional (ưu đãi, call-to-action đăng ký)

3. Gợi ý best time to post cho từng kênh

Viết đầy đủ, cụ thể từng ngày, không bỏ sót."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_marketing_campaign_plan(month: str, goal: str, budget_vnd: int = 0) -> str:
    """Kế hoạch marketing tổng thể: campaigns, KPIs, phân bổ ngân sách, timeline."""
    budget_note = f"\nTổng ngân sách: {budget_vnd:,}đ".replace(",", ".") if budget_vnd > 0 else "\nNgân sách: linh hoạt theo kết quả"
    prompt = f"""Tạo KẾ HOẠCH MARKETING TỔNG THỂ cho Studio Flow {month}.
Mục tiêu chính: {goal}{budget_note}

Output cần có:
1. **Tổng quan chiến lược**: 2-3 câu định hướng tháng
2. **Danh sách campaigns** (2-4 campaign), mỗi campaign gồm:
   - Tên campaign | Mục tiêu cụ thể | Kênh triển khai | Timeline | KPI đo lường
3. **Phân bổ ngân sách** theo kênh (% hoặc số tiền cụ thể)
4. **KPIs tổng thể tháng**: reach, clicks, leads, conversions, CAC mục tiêu
5. **Điểm nhấn khác biệt** so tháng trước

Thực tế, khả thi cho startup SaaS giai đoạn early-growth."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_kol_plan(month: str, num_kols: int = 3, platforms: str = "TikTok, Facebook") -> str:
    """Kế hoạch KOL/KOC: danh sách tier, brief ngắn, timeline tiếp cận, KPIs."""
    prompt = f"""Tạo KẾ HOẠCH KOL/KOC cho Studio Flow {month}.
Số lượng KOL: {num_kols} | Kênh: {platforms}

Output cần có:
1. **Tiêu chí chọn KOL**: follower range, engagement rate, niche phù hợp
2. **Danh sách {num_kols} profile KOL gợi ý** (loại KOL, không cần tên thật):
   - Loại KOL | Tier (nano/micro/mid) | Platform | Followers ước tính | Content style | Lý do phù hợp
3. **Timeline tiếp cận**:
   - Tuần 1: Research & outreach
   - Tuần 2: Brief & negotiate
   - Tuần 3-4: Content production & publish
4. **Brief ngắn gửi KOL**: key messages, dos & don'ts, deliverables
5. **KPIs**: views target, engagement rate, click-through, leads từ KOL
6. **Budget estimate** cho từng tier

Focus vào KOL ngành nhiếp ảnh, studio, wedding photography Việt Nam."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_paid_ads_plan(month: str, total_budget_vnd: int = 0, goal: str = "conversion") -> str:
    """Kế hoạch quảng cáo trả phí: Facebook Ads + Zalo Ads, targeting, budget/ngày, A/B test."""
    budget_str = f"{total_budget_vnd:,}đ".replace(",", ".") if total_budget_vnd > 0 else "tự đề xuất"
    prompt = f"""Tạo KẾ HOẠCH QUẢNG CÁO TRẢ PHÍ cho Studio Flow {month}.
Tổng ngân sách: {budget_str} | Mục tiêu: {goal}

Output cần có:
1. **Phân bổ ngân sách theo kênh**: Facebook Ads vs Zalo Ads (% + số tiền/ngày)
2. **Facebook Ads**:
   - Campaign structure (Awareness → Consideration → Conversion)
   - Targeting chi tiết: demographics, interests, behaviors phù hợp chủ studio VN
   - Ad formats: carousel, video, lead form — loại nào cho mục tiêu nào
   - Gợi ý creative: headline, primary text, CTA
   - A/B test plan: test gì trong tháng này
3. **Zalo Ads**:
   - Loại quảng cáo phù hợp
   - Targeting theo location và nghề nghiệp
4. **Lịch chạy ads**: tuần nào boost mạnh, tuần nào duy trì
5. **KPIs**: CPM, CPC, CPL, ROAS mục tiêu
6. **Retargeting plan**: pixel events, custom audiences cần tạo"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_pr_communications_plan(month: str, events: str = "") -> str:
    """Kế hoạch PR/truyền thông: group seeding, community, báo chí, events nội bộ."""
    events_note = f"\nSự kiện trong tháng: {events}" if events else ""
    prompt = f"""Tạo KẾ HOẠCH PR & TRUYỀN THÔNG cho Studio Flow {month}.{events_note}

Output cần có:
1. **Group seeding plan**:
   - Danh sách loại group Facebook phù hợp (nhiếp ảnh, kinh doanh, startup VN)
   - Tần suất post | Loại nội dung cho từng group | Cách tránh bị spam
2. **Community management**:
   - Kế hoạch engage trên fanpage (reply comments, inbox policy)
   - Cách xử lý feedback tiêu cực
3. **Báo chí & media** (nếu có):
   - Pitching angle cho tháng này
   - Danh sách media/blog phù hợp để tiếp cận
4. **Word-of-mouth & referral**:
   - Kế hoạch kích hoạt user hiện tại review/share
   - Referral program nếu có
5. **Nội dung viral tiềm năng**: 1-2 ý tưởng content có thể viral trong ngành
6. **Lịch PR theo tuần**: hoạt động cụ thể từng tuần

Phù hợp thị trường studio chụp ảnh Việt Nam."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_sales_business_plan(month: str, lead_target: int = 50, pro_conversion_target: int = 20) -> str:
    """Kế hoạch kinh doanh: lead pipeline, outreach script, follow-up schedule, targets."""
    prompt = f"""Tạo KẾ HOẠCH KINH DOANH & SALES cho Studio Flow {month}.
Target: {lead_target} leads mới | {pro_conversion_target} user chuyển lên Pro

Output cần có:
1. **Pipeline targets theo tuần**:
   - Leads mới | Demos/calls | Trial activations | Conversions to Pro
2. **Nguồn lead**:
   - Inbound (từ content, ads, KOL): % ước tính
   - Outbound (cold outreach): target số lượng/tuần, kênh tiếp cận
3. **Outreach script mẫu**:
   - DM Facebook/Zalo cho chủ studio chưa biết Studio Flow
   - Follow-up message cho user Free chưa upgrade
4. **Free → Pro conversion plan**:
   - Trigger points để offer upgrade
   - Email/message sequence 7 ngày sau đăng ký Free
   - Incentive/promotion nếu có
5. **Chỉ số theo dõi hàng tuần**: số lead, conversion rate, churn rate
6. **Action items cho sales team**: việc cụ thể mỗi ngày/tuần

Thực tế cho team nhỏ (1-3 người) giai đoạn early-stage."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def create_master_timeline(month: str, all_plans_summary: str) -> str:
    """Timeline tổng hợp dạng bảng tuần: ghép tất cả activities vào 1 calendar view."""
    prompt = f"""Tạo MASTER TIMELINE tổng hợp cho Studio Flow {month}.

Dựa trên các kế hoạch đã có:
{all_plans_summary}

Tạo 1 bảng timeline tổng hợp dạng:

| Tuần | Content & Social | Marketing Campaigns | KOL | Paid Ads | PR | Sales | Ghi chú |
|---|---|---|---|---|---|---|---|
| Tuần 1 (ngày X-Y) | ... | ... | ... | ... | ... | ... | ... |
| Tuần 2 | ... | ... | ... | ... | ... | ... | ... |
| Tuần 3 | ... | ... | ... | ... | ... | ... | ... |
| Tuần 4 | ... | ... | ... | ... | ... | ... | ... |

Sau bảng, thêm:
1. **Top 3 ưu tiên của tháng** (việc quan trọng nhất cần làm ngay)
2. **Checklist kick-off** (việc cần chuẩn bị trước ngày 1 của tháng)
3. **KPIs tổng hợp** (bảng 1 trang gồm tất cả chỉ số cần đạt)

Ngắn gọn, dễ đọc, phù hợp in ra dán tường team."""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=4096,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
