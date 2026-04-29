"""
Skill: Content Writing
Tạo nội dung marketing chất lượng cao cho Studio Flow sử dụng Claude API với Prompt Caching
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT

_client = get_client()

# System prompt dùng cache — chỉ tốn token 1 lần mỗi 5 phút
CACHED_SYSTEM = [
    {
        "type": "text",
        "text": STUDIOFLOW_CONTEXT,
        "cache_control": {"type": "ephemeral"},
    }
]


def write_facebook_post(topic: str, post_type: str = "educational", include_cta: bool = True) -> str:
    """
    Viết bài đăng Facebook cho Studio Flow.

    Args:
        topic: Chủ đề bài viết
        post_type: educational | promotional | testimonial | tip | announcement
        include_cta: Thêm call-to-action hay không
    """
    cta_instruction = "Kết thúc bằng CTA mời dùng thử miễn phí tại studioflow.vn" if include_cta else ""

    prompt = f"""
Viết 1 bài đăng Facebook về chủ đề: "{topic}"
Loại bài: {post_type}
{cta_instruction}

Yêu cầu:
- Dài 150–250 từ
- Dùng emoji phù hợp (không quá 5 cái)
- Ngôn ngữ thân thiện, gần gũi với chủ studio Việt Nam
- Có thể dùng hashtag cuối bài (tối đa 5 hashtag)
- Không dùng từ ngữ cứng nhắc, máy móc
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=600,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def write_blog_article(title: str, keywords: list[str], word_count: int = 800) -> str:
    """Viết bài blog SEO cho studioflow.vn."""
    kw_str = ", ".join(keywords)
    prompt = f"""
Viết bài blog SEO với tiêu đề: "{title}"
Từ khóa chính: {kw_str}
Độ dài: khoảng {word_count} từ

Cấu trúc: H1 (tiêu đề) → Intro 2 đoạn → 3-4 mục H2 với nội dung chi tiết → Kết luận + CTA
Tối ưu SEO tự nhiên, không nhồi nhét từ khóa.
Viết cho đối tượng: chủ studio chụp ảnh Việt Nam, ít rành công nghệ.
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=2000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def write_email_campaign(campaign_type: str, recipient_segment: str) -> dict:
    """
    Viết email marketing.

    Args:
        campaign_type: welcome | upgrade_pro | upgrade_business | win_back | feature_announcement
        recipient_segment: free_user | pro_user | lead | churned_user
    """
    prompt = f"""
Viết email marketing cho Studio Flow:
Loại campaign: {campaign_type}
Phân khúc người nhận: {recipient_segment}

Trả về JSON với cấu trúc:
{{
  "subject": "Tiêu đề email (dưới 60 ký tự)",
  "preview_text": "Preview text (dưới 90 ký tự)",
  "body": "Nội dung email HTML đầy đủ"
}}

Yêu cầu: Cá nhân hóa, ngắn gọn (dưới 200 từ body text), có 1 CTA button rõ ràng.
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=1000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def write_ad_copy(platform: str, objective: str, product_feature: str) -> dict:
    """
    Viết copy quảng cáo cho Facebook/Google Ads.

    Args:
        platform: facebook | google | zalo
        objective: awareness | conversion | retargeting
        product_feature: tính năng muốn highlight
    """
    prompt = f"""
Viết copy quảng cáo cho {platform.upper()}, mục tiêu {objective}.
Highlight tính năng: {product_feature}

Trả về các phiên bản:
1. Primary text (125 ký tự)
2. Headline (40 ký tự)
3. Description (30 ký tự)
4. Long form version (cho Facebook, 200 ký tự)

Format: JSON với keys primary, headline, description, long_form
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=500,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_content_calendar(month: str, posts_per_week: int = 4) -> str:
    """Tạo lịch nội dung cho 1 tháng."""
    prompt = f"""
Tạo lịch nội dung Facebook cho Studio Flow tháng {month}.
Số bài/tuần: {posts_per_week}
Tổng bài: {posts_per_week * 4} bài

Phân bổ loại bài:
- 40% Educational (tips quản lý studio, kiến thức nghề)
- 25% Product feature showcase
- 20% Social proof / Testimonial
- 15% Promotional / Offer

Format bảng: Ngày | Loại bài | Chủ đề | Caption ngắn | Gợi ý hình ảnh
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=2000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
