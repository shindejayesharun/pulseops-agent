import json
from typing import Any, Dict, List
import openai
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.providers.base import BaseLLMProvider
from app.config import settings


class OpenAILLMProvider(BaseLLMProvider):
    """
    Production-grade LLM provider adapter using the official OpenAI SDK.
    Fully compatible with OpenAI models (gpt-4o, gpt-4o-mini) and Grok/xAI via base_url.
    """

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "grok":
            self.client = openai.OpenAI(
                api_key=settings.xai_api_key or "missing_key",
                base_url=settings.xai_base_url
            )
            self.model = settings.xai_model
        else:
            self.client = openai.OpenAI(
                api_key=settings.openai_api_key or "missing_key"
            )
            self.model = settings.openai_model

    def plan_next_step(
        self,
        messages: List[Dict[str, Any]],
        tool_definitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Prepend system prompt if not present
        formatted_messages = []
        has_system = any(m.get("role") == "system" for m in messages)
        if not has_system:
            formatted_messages.append({"role": "system", "content": SYSTEM_PROMPT})

        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role == "tool":
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": m.get("tool_call_id", "default_id"),
                    "name": m.get("name"),
                    "content": json.dumps(content) if not isinstance(content, str) else content
                })
            elif role == "assistant" and "tool_calls" in m:
                formatted_messages.append({
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": m.get("tool_calls")
                })
            else:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=tool_definitions if tool_definitions else None,
                tool_choice="auto" if tool_definitions else None,
                temperature=0.1
            )
        except Exception as e:
            return {
                "type": "final_answer",
                "content": f"LLM Provider Error ({self.provider}): {str(e)}"
            }

        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            calls = []
            for tc in msg.tool_calls:
                try:
                    parsed_args = json.loads(tc.function.arguments)
                except Exception:
                    parsed_args = {}
                calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": parsed_args
                })
            return {
                "type": "tool_calls",
                "tool_calls": calls
            }
        else:
            return {
                "type": "final_answer",
                "content": msg.content or ""
            }
