"""
Orchestrator Agent — Studio Flow AI Marketing System
Agent điều phối trung tâm, nhận request và phân công cho đúng agent chuyên biệt
"""
from llm_client import get_client
from config import config, STUDIOFLOW_CONTEXT
from agents.content_agent import run_content_agent
from agents.kol_agent import run_kol_agent
from agents.business_analyst_agent import run_business_analyst_agent

_client = get_client()

ORCHESTRATOR_TOOLS = [
    {
        "name": "run_content_agent",
        "description": (
            "Giao việc cho Content Marketing Agent. Phù hợp cho: "
            "viết bài Facebook, blog SEO, email, ad copy, content calendar, tạo hình ảnh marketing"
        ),
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string", "description": "Nhiệm vụ cụ thể"}},
            "required": ["task"],
        },
    },
    {
        "name": "run_kol_agent",
        "description": (
            "Giao việc cho KOL/KOC Campaign Agent. Phù hợp cho: "
            "tạo kịch bản TikTok/Reels/YouTube, brief KOL, outreach message, chiến lược KOL"
        ),
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
    {
        "name": "run_business_analyst",
        "description": (
            "Giao việc cho Business Analyst Agent. Phù hợp cho: "
            "phân tích đối thủ, phân khúc khách hàng, chiến lược tăng trưởng, báo cáo, tìm lead"
        ),
        "input_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
    },
]


def run_orchestrator(request: str) -> str:
    """
    Entry point chính — nhận bất kỳ request nào và tự phân công agent phù hợp.

    Ví dụ request:
    - "Chuẩn bị toàn bộ cho campaign ra mắt tính năng GPS tháng 5"
    - "Tôi cần nội dung Facebook tuần này và phân tích tại sao user churn cao"
    - "Tạo kịch bản KOL và brief cho 3 KOL micro trên TikTok"
    """
    messages = [{"role": "user", "content": request}]
    initial_message = messages[0]

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là ORCHESTRATOR — AI Marketing Director của Studio Flow.
Bạn điều phối team AI gồm 3 agent chuyên biệt:
1. Content Agent — Tạo nội dung marketing (bài viết, blog, ads, calendar, hình ảnh)
2. KOL/KOC Agent — Kịch bản, brief, chiến lược KOL/KOC
3. Business Analyst Agent — Nghiên cứu thị trường, phân tích, chiến lược

Khi nhận request:
1. Phân tích xem cần agent nào (có thể nhiều agent)
2. Phân chia task rõ ràng cho từng agent
3. Tổng hợp kết quả cuối cùng thành báo cáo cohesive

Luôn bắt đầu bằng kế hoạch ngắn gọn: "Tôi sẽ giao task cho..."
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    print(f"\n{'='*60}")
    print(f"[ORCHESTRATOR] Nhận request: {request}")
    print(f"{'='*60}\n")

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
            tools=ORCHESTRATOR_TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text"):
                print(f"[Director]: {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n{'─'*40}")
                    print(f"[Delegating to] → {block.name.replace('run_', '').upper()}")
                    print(f"[Task]: {block.input.get('task', '')[:150]}")
                    print(f"{'─'*40}")

                    if block.name == "run_content_agent":
                        result = run_content_agent(block.input["task"])
                    elif block.name == "run_kol_agent":
                        result = run_kol_agent(block.input["task"])
                    elif block.name == "run_business_analyst":
                        result = run_business_analyst_agent(block.input["task"])
                    else:
                        result = f"Agent {block.name} không tồn tại"

                    result_str = str(result)
                    if len(result_str) > 3000:
                        result_str = result_str[:2900] + "... [truncated]"
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
    print("Studio Flow — AI Marketing System")
    print("Nhập request (hoặc 'quit' để thoát):\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ("quit", "exit", "thoat"):
            break
        if not user_input:
            continue
        result = run_orchestrator(user_input)
        print(f"\n{'='*60}\n[KẾT QUẢ]\n{result}\n{'='*60}\n")
