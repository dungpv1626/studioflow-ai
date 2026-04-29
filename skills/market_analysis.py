"""
Skill: Market Analysis & Business Intelligence
Phân tích thị trường, đối thủ, khách hàng cho Studio Flow
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from skills.web_scraping import scrape_google_search, scrape_facebook_page

_client = get_client()

CACHED_SYSTEM = [
    {
        "type": "text",
        "text": STUDIOFLOW_CONTEXT + """

VAI TRÒ: Business Analyst & Market Intelligence Expert
Bạn chuyên phân tích thị trường SaaS B2B tại Việt Nam, đặc biệt ngành nhiếp ảnh.
Luôn đưa ra insight actionable, không chỉ mô tả dữ liệu.
""",
        "cache_control": {"type": "ephemeral"},
    }
]


def analyze_competitor(competitor_name: str, competitor_url: str | None = None) -> str:
    """Phân tích đối thủ cạnh tranh của Studio Flow."""
    # Thu thập dữ liệu từ Google nếu có API
    search_results = []
    if config.APIFY_API_TOKEN:
        try:
            search_results = scrape_google_search(
                f"{competitor_name} phần mềm quản lý studio chụp ảnh review",
                max_results=10,
            )
        except Exception:
            pass

    context = f"Tên đối thủ: {competitor_name}"
    if competitor_url:
        context += f"\nWebsite: {competitor_url}"
    if search_results:
        context += f"\n\nDữ liệu thu thập được:\n{str(search_results[:5])}"

    prompt = f"""
{context}

Phân tích đối thủ cho Studio Flow theo framework:

1. **Tổng quan** — Sản phẩm/dịch vụ, thị trường mục tiêu, định vị
2. **Bảng giá & Gói dịch vụ** — So sánh với Studio Flow (Free/299k/499k)
3. **Điểm mạnh của đối thủ** — Họ làm tốt điều gì?
4. **Điểm yếu / Khoảng trống** — Nơi Studio Flow có thể tấn công
5. **Chiến lược Marketing** — Kênh, thông điệp, đối tượng họ đang nhắm
6. **Opportunities** — 3 cơ hội cụ thể cho Studio Flow từ phân tích này
7. **Threats** — 2-3 rủi ro cần chú ý

Kết luận với 1 chiến lược differentiation recommendation.
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=2000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def analyze_customer_segment(segment_data: str, segment_name: str) -> str:
    """Phân tích phân khúc khách hàng."""
    prompt = f"""
Phân tích phân khúc khách hàng cho Studio Flow:

Phân khúc: {segment_name}
Dữ liệu: {segment_data}

Đầu ra:
1. **Persona** — Chân dung khách hàng điển hình
2. **Jobs-to-be-done** — Họ thuê Studio Flow để làm gì?
3. **Pain Points** — 5 nỗi đau lớn nhất
4. **Gain Points** — Kết quả họ muốn đạt
5. **Hành trình mua hàng** — Từ awareness → purchase → retention
6. **Kênh tiếp cận tốt nhất** — Nơi họ thường xuyên online
7. **Thông điệp marketing hiệu quả** — 3 angle khác nhau
8. **Rào cản chuyển đổi** — Tại sao họ chưa dùng / bỏ sản phẩm

Recommendation: Chiến lược acquisition cho phân khúc này.
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=1500,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_growth_strategy(
    current_metrics: dict,
    timeframe: str = "Q3 2025",
    focus_area: str = "user_acquisition",
) -> str:
    """
    Tạo chiến lược tăng trưởng dựa trên dữ liệu hiện tại.

    Args:
        current_metrics: Dict chứa các chỉ số hiện tại (users, MRR, churn, etc.)
        timeframe: Khung thời gian mục tiêu
        focus_area: user_acquisition | revenue_growth | churn_reduction | expansion
    """
    metrics_str = "\n".join([f"- {k}: {v}" for k, v in current_metrics.items()])

    prompt = f"""
Xây dựng chiến lược tăng trưởng cho Studio Flow:

METRICS HIỆN TẠI:
{metrics_str}

THỜI GIAN: {timeframe}
TRỌNG TÂM: {focus_area}

Chiến lược phải bao gồm:

## 1. PHÂN TÍCH HIỆN TRẠNG
- Đánh giá sức khỏe sản phẩm từ metrics
- Bottleneck lớn nhất hiện tại

## 2. MỤC TIÊU (SMART)
- KPI cụ thể cho {timeframe}
- Benchmark thị trường SaaS Đông Nam Á

## 3. CHIẾN LƯỢC TĂNG TRƯỞNG
Ít nhất 3 growth levers:
- Quick wins (thực hiện được trong 2 tuần)
- Medium term (1-3 tháng)
- Long term (3-6 tháng)

## 4. MARKETING CHANNELS PRIORITY
- Rank theo ROI dự kiến cho thị trường Việt Nam

## 5. PRICING STRATEGY
- Có nên điều chỉnh gói Free/Pro/Business không?

## 6. ROADMAP THỰC HIỆN
- Tuần 1-4: Actions cụ thể
- Owner cho từng action

## 7. BUDGET ALLOCATION (%)
- Phân bổ ngân sách marketing theo kênh
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=3000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def analyze_market_trends(raw_data: str, data_source: str) -> str:
    """Phân tích xu hướng thị trường từ dữ liệu thu thập."""
    prompt = f"""
Phân tích xu hướng thị trường cho ngành quản lý studio Việt Nam.

Nguồn dữ liệu: {data_source}
Dữ liệu raw:
{raw_data[:3000]}

Đầu ra:
1. **Xu hướng nổi bật** — Top 5 trends từ dữ liệu
2. **Nhu cầu chưa được đáp ứng** — Gaps trong thị trường
3. **Cơ hội sản phẩm** — Feature/tính năng mới cho Studio Flow
4. **Cơ hội marketing** — Angle mới, audience mới
5. **Early signals** — Xu hướng nhỏ nhưng có thể lớn trong 6-12 tháng

Format: Executive summary ngắn gọn + Chi tiết từng điểm.
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=1500,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
