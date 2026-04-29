import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini (thay thế Anthropic — có free tier)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = GEMINI_API_KEY  # alias để không sửa code cũ
    CLAUDE_DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-6")
    CLAUDE_ANALYSIS_MODEL = os.getenv("CLAUDE_ANALYSIS_MODEL", "claude-opus-4-7")
    CLAUDE_FAST_MODEL = os.getenv("CLAUDE_FAST_MODEL", "claude-haiku-4-5-20251001")
    ENABLE_PROMPT_CACHE = os.getenv("ENABLE_PROMPT_CACHE", "true").lower() == "true"

    # Kie AI
    KIE_AI_API_KEY = os.getenv("KIE_AI_API_KEY", "")
    KIE_AI_BASE_URL = os.getenv("KIE_AI_BASE_URL", "https://api.kie.ai/v1")

    # Apify
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
    APIFY_BASE_URL = os.getenv("APIFY_BASE_URL", "https://api.apify.com/v2")

    # Facebook
    FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
    FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")

    # Business
    BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Studio Flow")
    BUSINESS_WEBSITE = os.getenv("BUSINESS_WEBSITE", "https://studioflow.vn")
    BUSINESS_FACEBOOK = os.getenv("BUSINESS_FACEBOOK", "https://web.facebook.com/studioflowtech")
    BUSINESS_ZALO = os.getenv("BUSINESS_ZALO", "0965867228")
    FOUNDER_NAME = os.getenv("FOUNDER_NAME", "Dũng Phạm")

    CONTENT_LANGUAGE = os.getenv("CONTENT_LANGUAGE", "vi")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()

STUDIOFLOW_CONTEXT = f"""
Bạn là AI Assistant của {config.BUSINESS_NAME} — nền tảng quản lý studio chụp ảnh toàn diện tại Việt Nam.

Thông tin doanh nghiệp:
- Tên: {config.BUSINESS_NAME}
- Founder: {config.FOUNDER_NAME}
- Website: {config.BUSINESS_WEBSITE}
- Facebook: {config.BUSINESS_FACEBOOK}
- Zalo: {config.BUSINESS_ZALO}

Sản phẩm chính:
- Phần mềm SaaS quản lý studio chụp ảnh
- Tính năng: Quản lý khách hàng, Lịch hẹn, Hóa đơn & Thanh toán, Báo cáo tài chính
- Bảng giá: Free (miễn phí), Pro (299.000đ/tháng), Business (499.000đ/tháng)

Thị trường mục tiêu: Các studio chụp ảnh tại Việt Nam (ảnh cưới, ảnh sản phẩm, ảnh chân dung)
Tone of voice: Chuyên nghiệp nhưng gần gũi, thân thiện với người dùng Việt Nam
"""
