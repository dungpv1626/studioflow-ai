"""
Agent: KOL/KOC Campaign Agent
Quản lý toàn bộ quy trình KOL/KOC: tìm kiếm, brief, kịch bản, tracking
"""
import json
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from skills.kol_koc_scripts import (
    generate_tiktok_script,
    generate_facebook_live_script,
    generate_youtube_review_script,
    generate_kol_brief,
    generate_kol_outreach_message,
    KOL_PERSONAS,
)
from skills.web_scraping import scrape_tiktok_hashtag

_client = get_client()

KOL_TOOLS = [
    {
        "name": "generate_tiktok_script",
        "description": "Tạo kịch bản TikTok/Reels hoàn chỉnh cho KOL",
        "input_schema": {
            "type": "object",
            "properties": {
                "kol_profile": {"type": "string", "description": "Mô tả KOL"},
                "video_concept": {"type": "string", "description": "Ý tưởng video"},
                "duration_seconds": {"type": "integer", "default": 60},
                "style": {
                    "type": "string",
                    "enum": ["authentic_review", "tutorial", "day_in_life", "problem_solution", "transformation"],
                    "default": "authentic_review",
                },
            },
            "required": ["kol_profile", "video_concept"],
        },
    },
    {
        "name": "generate_facebook_live_script",
        "description": "Tạo kịch bản Facebook Live chi tiết",
        "input_schema": {
            "type": "object",
            "properties": {
                "host_profile": {"type": "string"},
                "live_duration_minutes": {"type": "integer", "default": 30},
                "objective": {
                    "type": "string",
                    "enum": ["product_demo", "q_and_a", "tutorial", "launch_event"],
                    "default": "product_demo",
                },
            },
            "required": ["host_profile"],
        },
    },
    {
        "name": "generate_youtube_review_script",
        "description": "Tạo kịch bản YouTube review dài",
        "input_schema": {
            "type": "object",
            "properties": {
                "reviewer_profile": {"type": "string"},
                "video_title": {"type": "string"},
                "duration_minutes": {"type": "integer", "default": 10},
            },
            "required": ["reviewer_profile", "video_title"],
        },
    },
    {
        "name": "generate_kol_brief",
        "description": "Tạo brief gửi cho KOL/KOC chuyên nghiệp",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string"},
                "kol_tier": {
                    "type": "string",
                    "enum": ["nano", "micro", "macro", "mega"],
                    "default": "micro",
                },
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "facebook", "youtube", "instagram"],
                },
                "budget_range": {"type": "string", "default": "1-3 triệu đồng"},
            },
            "required": ["campaign_name", "platform"],
        },
    },
    {
        "name": "generate_outreach_message",
        "description": "Viết tin nhắn tiếp cận KOL lần đầu",
        "input_schema": {
            "type": "object",
            "properties": {
                "kol_name": {"type": "string"},
                "platform": {"type": "string"},
                "follower_count": {"type": "string"},
            },
            "required": ["kol_name", "platform", "follower_count"],
        },
    },
    {
        "name": "find_potential_kols",
        "description": "Tìm kiếm KOL tiềm năng trong ngành nhiếp ảnh qua TikTok hashtag",
        "input_schema": {
            "type": "object",
            "properties": {
                "hashtag": {"type": "string", "description": "Hashtag không có dấu #"},
                "max_results": {"type": "integer", "default": 20},
            },
            "required": ["hashtag"],
        },
    },
    {
        "name": "get_kol_persona",
        "description": "Lấy thông tin persona KOL mẫu đã có sẵn",
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_type": {
                    "type": "string",
                    "enum": list(KOL_PERSONAS.keys()),
                },
            },
            "required": ["persona_type"],
        },
    },
]


def _execute_kol_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "generate_tiktok_script":
        return generate_tiktok_script(**tool_input)
    elif tool_name == "generate_facebook_live_script":
        return generate_facebook_live_script(**tool_input)
    elif tool_name == "generate_youtube_review_script":
        return generate_youtube_review_script(**tool_input)
    elif tool_name == "generate_kol_brief":
        return generate_kol_brief(**tool_input)
    elif tool_name == "generate_outreach_message":
        return generate_kol_outreach_message(**tool_input)
    elif tool_name == "find_potential_kols":
        if not config.APIFY_API_TOKEN:
            return "APIFY_API_TOKEN chưa được cấu hình. Hãy thêm vào file .env"
        data = scrape_tiktok_hashtag(tool_input["hashtag"], tool_input.get("max_results", 20))
        return json.dumps(data[:5], ensure_ascii=False)
    elif tool_name == "get_kol_persona":
        persona = KOL_PERSONAS.get(tool_input["persona_type"], {})
        return json.dumps(persona, ensure_ascii=False)
    return f"Tool {tool_name} không được hỗ trợ"


def run_kol_agent(task: str) -> str:
    """
    Chạy KOL/KOC Campaign Agent.

    Ví dụ task:
    - "Tạo kịch bản TikTok 60s cho KOL là nhiếp ảnh gia ảnh cưới tại Hà Nội, phong cách authentic review"
    - "Tạo brief đầy đủ cho campaign ra mắt tính năng Chấm Công GPS, KOL micro trên TikTok"
    - "Chuẩn bị toàn bộ campaign KOL cho tháng 5: brief, kịch bản TikTok, FB Live, và outreach message"
    """
    messages = [{"role": "user", "content": task}]
    initial_message = messages[0]

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là KOL/KOC Campaign Manager của Studio Flow.
Nhiệm vụ: Lập kế hoạch và thực thi các campaign KOL/KOC hiệu quả nhất cho thị trường Việt Nam.
Ưu tiên KOL trong ngành nhiếp ảnh (ảnh cưới, portrait, commercial photography).
Sau mỗi bước, báo cáo ngắn gọn những gì đã làm.
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    print(f"\n[KOL Agent] Task: {task}\n")

    MAX_ITERATIONS = 10
    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        if len(messages) > 7:
            messages = [initial_message] + messages[-6:]

        response = _client.messages.create(
            model=config.CLAUDE_DEFAULT_MODEL,
            max_tokens=4096,
            system=system,
            tools=KOL_TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text"):
                print(f"[Agent]: {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n[Tool] {block.name}...")
                    result = _execute_kol_tool(block.name, block.input)
                    result_str = str(result)
                    if len(result_str) > 2000:
                        result_str = result_str[:1900] + "... [truncated]"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text
    return final_text


if __name__ == "__main__":
    result = run_kol_agent(
        "Tạo kịch bản TikTok 60 giây cho KOL là chủ studio ảnh cưới tại Hà Nội, "
        "concept: 'Ngày bận nhất trong đời tôi và cách Studio Flow cứu tôi'. "
        "Phong cách: problem_solution. Kèm brief ngắn cho KOL."
    )
    print("\n=== KẾT QUẢ ===")
    print(result)
