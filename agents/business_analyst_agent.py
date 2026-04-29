"""
Agent: Business Analyst Agent
Phân tích thị trường, đối thủ, khách hàng và tạo chiến lược tăng trưởng cho Studio Flow
"""
import json
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from skills.market_analysis import (
    analyze_competitor,
    analyze_customer_segment,
    generate_growth_strategy,
    analyze_market_trends,
)
from skills.web_scraping import (
    scrape_google_search,
    find_photography_studios_vietnam,
    COMPETITORS,
)

_client = get_client()

ANALYST_TOOLS = [
    {
        "name": "analyze_competitor",
        "description": "Phân tích chi tiết một đối thủ cạnh tranh của Studio Flow",
        "input_schema": {
            "type": "object",
            "properties": {
                "competitor_name": {"type": "string"},
                "competitor_url": {"type": "string"},
            },
            "required": ["competitor_name"],
        },
    },
    {
        "name": "analyze_customer_segment",
        "description": "Phân tích sâu một phân khúc khách hàng",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_name": {"type": "string", "description": "Tên phân khúc"},
                "segment_data": {"type": "string", "description": "Thông tin về phân khúc"},
            },
            "required": ["segment_name", "segment_data"],
        },
    },
    {
        "name": "generate_growth_strategy",
        "description": "Tạo chiến lược tăng trưởng dựa trên metrics",
        "input_schema": {
            "type": "object",
            "properties": {
                "current_metrics": {
                    "type": "object",
                    "description": "Metrics hiện tại: users, MRR, churn_rate, etc.",
                },
                "timeframe": {"type": "string", "default": "Q3 2025"},
                "focus_area": {
                    "type": "string",
                    "enum": ["user_acquisition", "revenue_growth", "churn_reduction", "expansion"],
                    "default": "user_acquisition",
                },
            },
            "required": ["current_metrics"],
        },
    },
    {
        "name": "search_market_data",
        "description": "Tìm kiếm dữ liệu thị trường qua Google",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Từ khóa tìm kiếm"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_potential_customers",
        "description": "Tìm danh sách studio chụp ảnh tiềm năng trên Google Maps",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "default": "Hà Nội"},
                "max_results": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "generate_pricing_analysis",
        "description": "Phân tích và đề xuất chiến lược giá cho Studio Flow",
        "input_schema": {
            "type": "object",
            "properties": {
                "market_data": {"type": "string", "description": "Dữ liệu giá của đối thủ"},
                "current_pricing": {
                    "type": "object",
                    "description": "Bảng giá hiện tại: Free/Pro 299k/Business 499k",
                },
            },
            "required": ["market_data"],
        },
    },
    {
        "name": "create_weekly_report",
        "description": "Tạo báo cáo tuần cho marketing và kinh doanh",
        "input_schema": {
            "type": "object",
            "properties": {
                "week": {"type": "string"},
                "metrics": {"type": "object"},
                "highlights": {"type": "string"},
            },
            "required": ["week"],
        },
    },
]


def _execute_analyst_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "analyze_competitor":
        return analyze_competitor(**tool_input)
    elif tool_name == "analyze_customer_segment":
        return analyze_customer_segment(**tool_input)
    elif tool_name == "generate_growth_strategy":
        return generate_growth_strategy(**tool_input)
    elif tool_name == "search_market_data":
        if not config.APIFY_API_TOKEN:
            return "APIFY chưa cấu hình. Trả về placeholder data."
        results = scrape_google_search(tool_input["query"], tool_input.get("max_results", 10))
        return json.dumps(results[:3], ensure_ascii=False)
    elif tool_name == "find_potential_customers":
        if not config.APIFY_API_TOKEN:
            return "APIFY chưa cấu hình."
        results = find_photography_studios_vietnam(
            tool_input.get("city", "Hà Nội"),
            tool_input.get("max_results", 50),
        )
        return json.dumps(results[:5], ensure_ascii=False)
    elif tool_name == "generate_pricing_analysis":
        return _pricing_analysis(**tool_input)
    elif tool_name == "create_weekly_report":
        return _create_weekly_report(**tool_input)
    return f"Tool {tool_name} không được hỗ trợ"


def _pricing_analysis(market_data: str, current_pricing: dict | None = None) -> str:
    """Phân tích giá sử dụng Claude."""
    current = current_pricing or {"Free": 0, "Pro": 299000, "Business": 499000}
    prompt = f"""
Phân tích chiến lược giá cho Studio Flow.
Giá hiện tại: {json.dumps(current, ensure_ascii=False)}
Dữ liệu thị trường: {market_data}

Đưa ra:
1. Đánh giá giá hiện tại so với thị trường
2. Có nên điều chỉnh không? Tại sao?
3. Gợi ý pricing strategy tối ưu (Value-based, Competitor-based, etc.)
4. Chiến thuật upsell Free → Pro và Pro → Business
"""
    from skills.market_analysis import _client as analysis_client
    response = analysis_client.messages.create(
        model=config.CLAUDE_ANALYSIS_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _create_weekly_report(week: str, metrics: dict | None = None, highlights: str = "") -> str:
    metrics_str = json.dumps(metrics or {}, ensure_ascii=False) if metrics else "Chưa có data"
    prompt = f"""
Tạo báo cáo tuần cho Studio Flow:
Tuần: {week}
Metrics: {metrics_str}
Highlights: {highlights}

Báo cáo theo format:
## 📊 TÓM TẮT TUẦN {week}
### KPIs chính
### Điểm nổi bật
### Vấn đề cần xử lý
### Kế hoạch tuần tới
"""
    from skills.market_analysis import _client as analysis_client
    response = analysis_client.messages.create(
        model=config.CLAUDE_DEFAULT_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def run_business_analyst_agent(task: str) -> str:
    """
    Chạy Business Analyst Agent.

    Ví dụ task:
    - "Phân tích top 3 đối thủ cạnh tranh của Studio Flow tại Việt Nam"
    - "Tạo chiến lược tăng trưởng Q3 2025 với mục tiêu tăng 200% user"
    - "Tìm 50 studio chụp ảnh tiềm năng tại Hà Nội và tạo kế hoạch outreach"
    - "Phân tích tại sao user free không chuyển lên Pro và đề xuất giải pháp"
    """
    messages = [{"role": "user", "content": task}]

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là Business Analyst & Growth Strategist của Studio Flow.
Nhiệm vụ: Phân tích thị trường, đối thủ, khách hàng và đưa ra chiến lược tăng trưởng cụ thể.
Luôn data-driven, actionable, và thực tế với thị trường Việt Nam.
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    print(f"\n[Business Analyst Agent] Task: {task}\n")

    while True:
        response = _client.messages.create(
            model=config.CLAUDE_ANALYSIS_MODEL,
            max_tokens=4096,
            system=system,
            tools=ANALYST_TOOLS,
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
                    result = _execute_analyst_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
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
    result = run_business_analyst_agent(
        "Phân tích phân khúc khách hàng 'chủ studio ảnh cưới' và đưa ra chiến lược "
        "marketing để convert họ từ Free lên Pro trong 30 ngày đầu."
    )
    print("\n=== KẾT QUẢ ===")
    print(result)
