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


def run_orchestrator(request: str, on_progress=None) -> tuple[str, list]:
    """
    Entry point chính — nhận bất kỳ request nào và tự phân công agent phù hợp.
    Returns: (final_text, collected_images) — images từ content_agent được gom lại.
    on_progress(msg): callback realtime cho Streamlit UI.
    """
    messages = [{"role": "user", "content": request}]
    initial_message = messages[0]
    collected_images = []  # gom ảnh từ content_agent

    def _log(msg):
        print(msg)
        if on_progress:
            on_progress(msg)

    system = [
        {
            "type": "text",
            "text": STUDIOFLOW_CONTEXT + """

Bạn là ORCHESTRATOR — AI Marketing Director của Studio Flow.
Bạn điều phối team AI gồm 3 agent chuyên biệt:
1. Content Agent — Tạo nội dung marketing (bài viết, blog, ads, calendar)
2. KOL/KOC Agent — Kịch bản, brief, chiến lược KOL/KOC
3. Business Analyst Agent — Nghiên cứu thị trường, phân tích, chiến lược

Khi nhận request:
1. Phân tích xem cần agent nào (có thể nhiều agent)
2. Phân chia task rõ ràng cho từng agent
3. Tổng hợp kết quả cuối cùng thành báo cáo cohesive

QUAN TRỌNG VỀ HÌNH ẢNH:
- Hệ thống kỹ thuật TỰ ĐỘNG tạo hình ảnh thực (JPEG có logo Studio Flow) sau khi Content Agent hoàn thành.
- Hình ảnh được hiển thị RIÊNG bên dưới văn bản trong giao diện — bạn KHÔNG thấy chúng trong tool result.
- TUYỆT ĐỐI KHÔNG nói "không thể tạo hình ảnh", "chỉ tạo mô tả", hay xin lỗi về hình ảnh.
- Trong tổng kết cuối, chỉ cần nói "Hình ảnh đã được tạo tự động kèm logo Studio Flow."

Luôn bắt đầu bằng kế hoạch ngắn gọn: "Tôi sẽ giao task cho..."
""",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    _log(f"\n[Orchestrator] Nhận request: {request[:100]}")


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
            if hasattr(block, "text") and block.text:
                _log(f"[Director]: {block.text[:200]}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    agent_label = block.name.replace("run_", "").replace("_", " ").title()
                    _log(f"\n→ Đang giao task cho {agent_label}...")

                    if block.name == "run_content_agent":
                        agent_out = run_content_agent(block.input["task"], on_progress=on_progress)
                        if isinstance(agent_out, tuple):
                            result_text_part, imgs = agent_out
                            # Giới hạn tổng ảnh tối đa 3 dù content_agent được gọi nhiều lần
                            slots_left = max(0, 3 - len(collected_images))
                            collected_images.extend(imgs[:slots_left])
                            result = result_text_part
                            _log(f"✓ Content Agent xong — thêm {min(len(imgs), slots_left)}/{len(imgs)} ảnh")
                        else:
                            result = agent_out
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
        if hasattr(block, "text") and block.text:
            final_text += block.text

    # Nếu đã có ảnh thực, xoá các đoạn Gemini viết sai về việc không thể tạo ảnh
    if collected_images:
        import re as _re
        false_patterns = [
            r'[^\n]*(?:không thể trực tiếp tạo|không thể tạo ra hình ảnh|chỉ giới hạn ở việc tạo.*mô tả|xin lỗi.*hình ảnh|bạn có thể sử dụng.*mô tả này để yêu cầu.*thiết kế)[^\n]*\n?',
        ]
        for pat in false_patterns:
            final_text = _re.sub(pat, '', final_text, flags=_re.IGNORECASE)
        final_text = final_text.strip()

    return final_text, collected_images


if __name__ == "__main__":
    print("Studio Flow — AI Marketing System")
    print("Nhập request (hoặc 'quit' để thoát):\n")

    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ("quit", "exit", "thoat"):
            break
        if not user_input:
            continue
        result_text, result_imgs = run_orchestrator(user_input)
        print(f"\n{'='*60}\n[KẾT QUẢ]\n{result_text}")
        if result_imgs:
            print(f"[IMAGES] {len(result_imgs)} ảnh đã tạo")
        print(f"{'='*60}\n")
