"""
Skill: KOL/KOC Script Generation
Tạo kịch bản chuyên nghiệp cho KOL/KOC quảng bá Studio Flow
trên TikTok, Facebook Reels, YouTube Shorts
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT

_client = get_client()

CACHED_SYSTEM = [
    {
        "type": "text",
        "text": STUDIOFLOW_CONTEXT + """

NHIỆM VỤ ĐẶC BIỆT — KOL/KOC SCRIPT WRITER:
Bạn là chuyên gia viết kịch bản cho KOL/KOC Việt Nam. Bạn hiểu:
- Cách nói chuyện tự nhiên, không đọc như robot
- Tâm lý người xem video ngắn (TikTok/Reels): 3 giây đầu quyết định tất cả
- Hook mạnh, storytelling hấp dẫn, CTA rõ ràng
- Ngôn ngữ đời thường của người Việt trẻ và chủ studio
""",
        "cache_control": {"type": "ephemeral"},
    }
]


def generate_tiktok_script(
    kol_profile: str,
    video_concept: str,
    duration_seconds: int = 60,
    style: str = "authentic_review",
) -> str:
    """
    Tạo kịch bản TikTok/Reels cho KOL/KOC.

    Args:
        kol_profile: Mô tả KOL (vd: "chủ studio ảnh cưới 5 năm kinh nghiệm, HN")
        video_concept: Ý tưởng video (vd: "review phần mềm quản lý studio")
        duration_seconds: Thời lượng video
        style: authentic_review | tutorial | day_in_life | problem_solution | transformation
    """
    prompt = f"""
Viết kịch bản TikTok/Reels CHI TIẾT cho KOL:

THÔNG TIN KOL: {kol_profile}
Ý TƯỞNG VIDEO: {video_concept}
THỜI LƯỢNG: {duration_seconds} giây
PHONG CÁCH: {style}

Kịch bản phải gồm:

1. **HOOK (0-3 giây)** — Câu mở đầu cực kỳ gây tò mò, đặt ngay vấn đề
2. **PROBLEM (3-15 giây)** — Kể nỗi đau thật mà chủ studio đang gặp
3. **STORY/DEMO (15-45 giây)** — Giới thiệu Studio Flow tự nhiên như người dùng thật
4. **RESULT (45-55 giây)** — Kết quả cụ thể, số liệu nếu có
5. **CTA (55-60 giây)** — Kêu gọi hành động rõ ràng

Định dạng:
- [THỜI GIAN] Lời thoại: "..."
- [HÀNH ĐỘNG]: mô tả cảnh quay / gestures
- [TEXT ON SCREEN]: chữ overlay xuất hiện
- [NHẠC]: gợi ý nhạc nền

⚠️ Viết lời thoại nghe như người thật nói, KHÔNG phải đọc quảng cáo!
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=1500,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_facebook_live_script(
    host_profile: str,
    live_duration_minutes: int = 30,
    objective: str = "product_demo",
) -> str:
    """
    Tạo kịch bản Facebook Live cho KOL/KOC hoặc founder demo sản phẩm.

    Args:
        host_profile: Thông tin người dẫn live
        live_duration_minutes: Thời lượng live
        objective: product_demo | q_and_a | tutorial | launch_event
    """
    prompt = f"""
Viết kịch bản Facebook Live CHI TIẾT:

NGƯỜI DẪN: {host_profile}
THỜI LƯỢNG: {live_duration_minutes} phút
MỤC TIÊU: {objective}

Kịch bản gồm các phần theo mốc thời gian:

[00:00 - 03:00] — WARM UP: Chào hỏi, tạo không khí
[03:00 - 08:00] — HOOK: Nêu vấn đề / reason to watch
[08:00 - {live_duration_minutes-10}:00] — NỘI DUNG CHÍNH: Demo / tutorial / nội dung
[{live_duration_minutes-10}:00 - {live_duration_minutes-5}:00] — Q&A và tương tác
[{live_duration_minutes-5}:00 - {live_duration_minutes}:00] — CTA và kết live

Mỗi phần có:
- Lời thoại mẫu (ngôn ngữ tự nhiên)
- Điểm tương tác với viewer (hỏi comment, reaction)
- Gợi ý quà tặng / mini game nếu phù hợp
- Điểm nhấn sản phẩm Studio Flow
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=2000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_youtube_review_script(
    reviewer_profile: str,
    video_title: str,
    duration_minutes: int = 10,
) -> str:
    """Tạo kịch bản YouTube review dài cho KOL."""
    prompt = f"""
Viết kịch bản YouTube review chuyên nghiệp:

REVIEWER: {reviewer_profile}
TIÊU ĐỀ: {video_title}
THỜI LƯỢNG: ~{duration_minutes} phút

CẤU TRÚC:
- Intro + Hook (0:00 - 0:45)
- Giới thiệu vấn đề / context (0:45 - 2:00)
- Demo tính năng từng phần (2:00 - 7:00)
  • Quản lý khách hàng
  • Lịch hẹn
  • Hóa đơn & thanh toán
  • Báo cáo
- Đánh giá ưu/nhược điểm thật (7:00 - 9:00)
- Kết luận + Pricing + CTA (9:00 - 10:00)

Bao gồm:
- Timestamp chính xác
- Lời thoại đầy đủ (nghe tự nhiên như người review thật)
- Gợi ý B-roll footage
- Cards và end screen description
- Description box template với links
"""
    response = _client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=3000,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_kol_brief(
    campaign_name: str,
    kol_tier: str = "micro",
    platform: str = "tiktok",
    budget_range: str = "1-3 triệu đồng",
) -> str:
    """
    Tạo brief gửi cho KOL/KOC.

    Args:
        campaign_name: Tên campaign
        kol_tier: nano (<10k followers) | micro (10k-100k) | macro (100k-1M) | mega (>1M)
        platform: tiktok | facebook | youtube | instagram
        budget_range: Ngân sách dự kiến
    """
    prompt = f"""
Tạo BRIEF gửi KOL/KOC đầy đủ và chuyên nghiệp:

Campaign: {campaign_name}
KOL Tier: {kol_tier} ({platform})
Budget: {budget_range}

Brief phải gồm:
1. **Mục tiêu campaign** — KPI cụ thể
2. **Thông điệp cốt lõi** — Key messages không được thay đổi
3. **Điểm bắt buộc phải đề cập** — Checklist
4. **Điều KHÔNG được làm** — Dos & Don'ts
5. **Yêu cầu kỹ thuật** — Video specs, link, hashtag, tag page
6. **Timeline** — Deadline gửi draft, thời gian đăng
7. **Deliverables** — Số lượng video/post
8. **Tracking links** — UTM parameters gợi ý
9. **Quy trình duyệt content** — Bước review trước đăng

Viết chuyên nghiệp như agency lớn, format Word/Google Doc.
"""
    response = _client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=1500,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_kol_outreach_message(kol_name: str, platform: str, follower_count: str) -> str:
    """Viết tin nhắn tiếp cận KOL/KOC lần đầu."""
    prompt = f"""
Viết tin nhắn DM tiếp cận KOL trên {platform}:
Tên KOL: {kol_name}
Followers: {follower_count}

Tin nhắn phải:
- Cá nhân hóa (đề cập content họ đã làm)
- Ngắn gọn (dưới 150 từ)
- Không nghe như spam
- Gợi ý hợp tác rõ ràng
- Kèm theo brief ngắn về Studio Flow
- CTA rõ ràng (nhắn lại để trao đổi thêm)

Viết 2 phiên bản: formal và casual.
"""
    response = _client.messages.create(
        model=config.CLAUDE_FAST_MODEL,
        max_tokens=600,
        system=CACHED_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# --- KOL Persona Templates ---
KOL_PERSONAS = {
    "wedding_photographer": {
        "profile": "Nhiếp ảnh gia ảnh cưới 5 năm kinh nghiệm, có studio riêng tại Hà Nội, 50k+ followers TikTok",
        "pain_points": ["quản lý lịch hẹn bị chồng chéo", "khách không nhớ lịch cọc", "tính tiền sai"],
        "best_platforms": ["tiktok", "facebook"],
    },
    "portrait_studio_owner": {
        "profile": "Chủ studio chụp ảnh gia đình, thời trang tại TP.HCM, 2 nhân viên, doanh thu 50-100tr/tháng",
        "pain_points": ["theo dõi hoa hồng nhân viên phức tạp", "hóa đơn viết tay dễ mất", "không có báo cáo"],
        "best_platforms": ["facebook", "youtube"],
    },
    "content_creator_photographer": {
        "profile": "Nhiếp ảnh gia kiêm content creator, chụp cho thương hiệu, freelance, 100k+ followers",
        "pain_points": ["quản lý nhiều dự án cùng lúc", "khó theo dõi thanh toán từng dự án"],
        "best_platforms": ["instagram", "tiktok"],
    },
}
