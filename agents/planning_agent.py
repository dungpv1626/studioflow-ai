"""
Agent: Monthly Planning Agent
Tạo bộ kế hoạch hoạt động tháng toàn diện cho team Studio Flow:
Đăng bài · Marketing · KOL · Paid Ads · PR · Sales · Master Timeline
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from skills.monthly_planning import (
    create_content_posting_plan,
    create_marketing_campaign_plan,
    create_kol_plan,
    create_paid_ads_plan,
    create_pr_communications_plan,
    create_sales_business_plan,
    create_master_timeline,
)

_client = get_client()

PLAN_TOOLS = [
    {
        "name": "create_content_posting_plan",
        "description": "Tạo lịch đăng bài chi tiết cho tháng: ngày đăng, kênh, chủ đề, caption, hashtag",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Ví dụ: Tháng 5/2025"},
                "posts_per_week": {"type": "integer", "default": 5},
                "focus_theme": {"type": "string", "description": "Chủ đề trọng tâm tháng này"},
            },
            "required": ["month"],
        },
    },
    {
        "name": "create_marketing_campaign_plan",
        "description": "Kế hoạch marketing tổng thể: campaigns, KPIs, phân bổ ngân sách theo kênh",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "goal": {"type": "string", "description": "Mục tiêu tháng, ví dụ: tăng 50 user Pro"},
                "budget_vnd": {"type": "integer", "default": 0, "description": "Ngân sách tổng (VND), 0 = linh hoạt"},
            },
            "required": ["month", "goal"],
        },
    },
    {
        "name": "create_kol_plan",
        "description": "Kế hoạch KOL/KOC: tiêu chí chọn, profile gợi ý, brief, timeline tiếp cận, KPIs",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "num_kols": {"type": "integer", "default": 3},
                "platforms": {"type": "string", "default": "TikTok, Facebook"},
            },
            "required": ["month"],
        },
    },
    {
        "name": "create_paid_ads_plan",
        "description": "Kế hoạch quảng cáo Facebook Ads và Zalo Ads: targeting, budget/ngày, lịch chạy, A/B test",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "total_budget_vnd": {"type": "integer", "default": 0},
                "goal": {
                    "type": "string",
                    "enum": ["awareness", "conversion", "retargeting"],
                    "default": "conversion",
                },
            },
            "required": ["month"],
        },
    },
    {
        "name": "create_pr_communications_plan",
        "description": "Kế hoạch PR và truyền thông: group seeding, community, báo chí, word-of-mouth",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "events": {"type": "string", "description": "Sự kiện nội bộ hoặc ngành trong tháng (nếu có)"},
            },
            "required": ["month"],
        },
    },
    {
        "name": "create_sales_business_plan",
        "description": "Kế hoạch kinh doanh: lead pipeline, outreach script, Free→Pro conversion, targets tuần",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "lead_target": {"type": "integer", "default": 50},
                "pro_conversion_target": {"type": "integer", "default": 20},
            },
            "required": ["month"],
        },
    },
    {
        "name": "create_master_timeline",
        "description": "Tổng hợp tất cả kế hoạch thành 1 master calendar/timeline theo tuần, kèm checklist và KPIs tổng hợp",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string"},
                "all_plans_summary": {
                    "type": "string",
                    "description": "Tóm tắt ngắn nội dung 6 plan đã tạo để tổng hợp vào timeline",
                },
            },
            "required": ["month", "all_plans_summary"],
        },
    },
]


def _execute_planning_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "create_content_posting_plan":
        return create_content_posting_plan(**tool_input)
    elif tool_name == "create_marketing_campaign_plan":
        return create_marketing_campaign_plan(**tool_input)
    elif tool_name == "create_kol_plan":
        return create_kol_plan(**tool_input)
    elif tool_name == "create_paid_ads_plan":
        return create_paid_ads_plan(**tool_input)
    elif tool_name == "create_pr_communications_plan":
        return create_pr_communications_plan(**tool_input)
    elif tool_name == "create_sales_business_plan":
        return create_sales_business_plan(**tool_input)
    elif tool_name == "create_master_timeline":
        return create_master_timeline(**tool_input)
    return f"Tool {tool_name} không tồn tại"


def run_planning_agent(task: str, on_progress=None) -> str:
    """
    Tạo bộ kế hoạch tháng toàn diện cho Studio Flow.
    Gọi tuần tự 7 tools: content → marketing → KOL → ads → PR → sales → master timeline.
    on_progress(msg): callback realtime cho Streamlit.
    """
    messages = [{"role": "user", "content": task}]
    initial_message = messages[0]

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là Monthly Planning Director của Studio Flow.
Nhiệm vụ: Tạo BỘ KẾ HOẠCH THÁNG đầy đủ cho toàn bộ team kinh doanh, marketing, truyền thông.

Quy trình BẮT BUỘC (gọi đúng thứ tự, không bỏ bước):
1. create_content_posting_plan → lịch đăng bài chi tiết từng ngày
2. create_marketing_campaign_plan → chiến lược, campaigns, KPIs tổng thể
3. create_kol_plan → kế hoạch influencer marketing
4. create_paid_ads_plan → kế hoạch quảng cáo trả phí Facebook/Zalo
5. create_pr_communications_plan → kế hoạch PR và truyền thông
6. create_sales_business_plan → kế hoạch kinh doanh và sales
7. create_master_timeline → tổng hợp tất cả thành 1 calendar (truyền all_plans_summary = tóm tắt 6 plan trên)

Quy tắc:
- Tự extract thông tin từ request: tháng, mục tiêu, ngân sách. KHÔNG hỏi lại.
- Sau khi có đủ 7 plan, trình bày kết quả hoàn chỉnh với heading rõ ràng.
- Mỗi section bắt đầu bằng: ## 1. Lịch đăng bài / ## 2. Marketing / ## 3. KOL / ## 4. Paid Ads / ## 5. PR / ## 6. Sales / ## 7. Master Timeline
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    def _log(msg):
        print(msg)
        if on_progress:
            on_progress(msg)

    _log(f"\n[Planning Agent] Bắt đầu: {task}\n")

    # Thu thập kết quả từng plan để tổng hợp vào master timeline
    plan_results: dict[str, str] = {}

    MAX_ITERATIONS = 15
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1

        if len(messages) > 7:
            messages = [initial_message] + messages[-6:]

        response = _client.messages.create(
            model=config.CLAUDE_DEFAULT_MODEL,
            max_tokens=4096,
            system=system,
            tools=PLAN_TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                _log(f"[Director]: {block.text[:200]}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            import time as _time
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    _log(f"\n[Plan] Đang tạo: {block.name.replace('create_', '').replace('_', ' ').title()}...")

                    full_result = _execute_planning_tool(block.name, block.input)
                    plan_results[block.name] = full_result

                    _log(f"[Plan] Xong ({len(full_result)} ký tự)")
                    # Chờ ngắn giữa các lần gọi LLM để tránh bị rate limit Gemini
                    _time.sleep(3)

                    # Truncate cho tool_result để tránh token overflow
                    result_str = full_result
                    if len(result_str) > 2000:
                        result_str = result_str[:1900] + "... [xem kết quả đầy đủ bên dưới]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    # Lấy text cuối cùng từ agent
    agent_summary = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            agent_summary += block.text

    # Tổng hợp output đầy đủ từ tất cả plan_results
    # (không bị truncate như tool_results)
    SECTION_MAP = {
        "create_content_posting_plan":    "## 📅 1. Lịch Đăng Bài Chi Tiết",
        "create_marketing_campaign_plan": "## 🎯 2. Kế Hoạch Marketing Tổng Thể",
        "create_kol_plan":                "## 🎬 3. Kế Hoạch KOL/KOC",
        "create_paid_ads_plan":           "## 💰 4. Kế Hoạch Quảng Cáo Trả Phí",
        "create_pr_communications_plan":  "## 📣 5. Kế Hoạch PR & Truyền Thông",
        "create_sales_business_plan":     "## 💼 6. Kế Hoạch Kinh Doanh & Sales",
        "create_master_timeline":         "## 🗓️ 7. Master Timeline Tổng Hợp",
    }

    month_label = _extract_month(task)
    output_parts = [f"# 📋 BỘ KẾ HOẠCH THÁNG — {month_label}\n*Được tạo bởi Studio Flow AI Planning Agent*\n\n---\n"]

    for tool_key, heading in SECTION_MAP.items():
        if tool_key in plan_results:
            output_parts.append(f"{heading}\n\n{plan_results[tool_key]}\n\n---\n")

    final_output = "\n".join(output_parts)

    _log(f"\n[Planning Agent] Hoàn thành! Tổng {len(plan_results)}/7 kế hoạch, {len(final_output)} ký tự.")
    return final_output


def _extract_month(task: str) -> str:
    """Trích xuất tháng từ task string."""
    import re
    m = re.search(r'tháng\s*(\d+)[/\-]?(\d{4})?', task.lower())
    if m:
        month_num = m.group(1)
        year = m.group(2) or "2025"
        return f"Tháng {month_num}/{year}"
    return "Tháng này"


if __name__ == "__main__":
    result = run_planning_agent(
        "Tạo plan tháng 5/2025 cho Studio Flow, mục tiêu tăng 50 user Pro, ngân sách ads 10 triệu đồng"
    )
    print("\n=== KẾT QUẢ ===")
    print(result[:3000])
