"""
LLM Client — Gemini backend với giao diện tương thích Anthropic SDK
Dùng Google Gemini qua OpenAI-compatible endpoint (miễn phí có free tier)
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Map Anthropic model names → Gemini model names
MODEL_MAP = {
    "claude-sonnet-4-6":         "models/gemini-2.5-flash",
    "claude-opus-4-7":           "models/gemini-2.5-flash",
    "claude-haiku-4-5-20251001": "models/gemini-2.5-flash",
}
FALLBACK_MODEL = "models/gemini-2.5-pro"


class ContentBlock:
    """Mô phỏng Anthropic ContentBlock"""
    def __init__(self, type, text=None, id=None, name=None, input=None):
        self.type = type
        self.text = text
        self.id = id
        self.name = name
        self.input = input or {}


class GeminiMessage:
    """Mô phỏng Anthropic Message response"""

    def __init__(self, openai_response):
        self._choice = openai_response.choices[0]
        self._content_blocks = self._build_blocks()

    def _build_blocks(self):
        blocks = []
        msg = self._choice.message
        if msg.content:
            blocks.append(ContentBlock(type="text", text=msg.content))
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    inp = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except (json.JSONDecodeError, TypeError):
                    inp = {}
                blocks.append(ContentBlock(
                    type="tool_use",
                    id=tc.id,
                    name=tc.function.name,
                    input=inp,
                ))
        if not blocks:
            blocks.append(ContentBlock(type="text", text=""))
        return blocks

    @property
    def content(self):
        return self._content_blocks

    @property
    def stop_reason(self):
        return "tool_use" if self._choice.finish_reason == "tool_calls" else "end_turn"


class MessagesAPI:
    def __init__(self, openai_client):
        self._client = openai_client

    # ── helpers ──────────────────────────────────────────────────────────────

    def _system_text(self, system):
        """Trích nội dung text từ system (string hoặc Anthropic-style list)"""
        if system is None:
            return None
        if isinstance(system, str):
            return system
        if isinstance(system, list):
            return "\n".join(
                b.get("text", "") for b in system if isinstance(b, dict) and "text" in b
            )
        return str(system)

    def _to_openai_messages(self, messages):
        """Chuyển đổi Anthropic message history → OpenAI format"""
        result = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "assistant" and isinstance(content, list):
                # Đây là list ContentBlock từ response trước — chuyển về OpenAI format
                text_parts, tool_calls = [], []
                for block in content:
                    if not hasattr(block, "type"):
                        continue
                    if block.type == "text" and block.text:
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append({
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json.dumps(block.input, ensure_ascii=False),
                            },
                        })
                oai_msg = {"role": "assistant", "content": " ".join(text_parts) or ""}
                if tool_calls:
                    oai_msg["tool_calls"] = tool_calls
                result.append(oai_msg)

            elif role == "user" and isinstance(content, list):
                # Tool results từ Anthropic format → OpenAI tool messages
                if content and all(
                    isinstance(i, dict) and i.get("type") == "tool_result" for i in content
                ):
                    for item in content:
                        result.append({
                            "role": "tool",
                            "tool_call_id": item["tool_use_id"],
                            "content": str(item.get("content", "")),
                        })
                else:
                    result.append({"role": "user", "content": str(content)})

            else:
                result.append({"role": role, "content": content if isinstance(content, str) else str(content)})

        return result

    def _convert_tools(self, tools):
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for t in tools
        ]

    # ── main method ───────────────────────────────────────────────────────────

    def create(self, model, max_tokens, messages, system=None, tools=None, **kwargs):
        mapped_model = MODEL_MAP.get(model, model)

        oai_messages = []
        sys_text = self._system_text(system)
        if sys_text:
            oai_messages.append({"role": "system", "content": sys_text})
        oai_messages.extend(self._to_openai_messages(messages))

        oai_tools = self._convert_tools(tools)

        kwargs_final = {"model": mapped_model, "max_tokens": max_tokens, "messages": oai_messages}
        if oai_tools:
            kwargs_final["tools"] = oai_tools

        import time
        from openai import APIStatusError
        for attempt in range(3):
            try:
                model_used = kwargs_final["model"] if attempt == 0 else FALLBACK_MODEL
                kwargs_final["model"] = model_used
                response = self._client.chat.completions.create(**kwargs_final)
                return GeminiMessage(response)
            except APIStatusError as e:
                if e.status_code == 503 and attempt < 2:
                    time.sleep(3)
                    continue
                raise


class GeminiClient:
    """Drop-in thay thế anthropic.Anthropic() — dùng Gemini ở backend"""

    def __init__(self, api_key=None):
        key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._openai = OpenAI(api_key=key, base_url=GEMINI_BASE_URL)
        self.messages = MessagesAPI(self._openai)


def get_client(api_key=None) -> GeminiClient:
    return GeminiClient(api_key=api_key)
