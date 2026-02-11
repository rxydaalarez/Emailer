from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List


from .config import OpenAIConfig


@dataclass
class LLMResult:
    summary: str
    formatted_email: str
    key_points: List[str]


class LLMClient:
    def __init__(self, config: OpenAIConfig):
        from openai import OpenAI

        self.client = OpenAI(api_key=config.api_key)
        self.model = config.model

    def synthesize(self, keyword: str, trigger_email: str, history_context: str) -> LLMResult:
        prompt = f"""
You are an investment intelligence assistant.

Task:
1) Read NEW UPDATE and CONTEXT.
2) Produce a concise synthesis for investment {keyword}.
3) Return JSON with keys:
   - summary (string)
   - key_points (array of strings)
   - formatted_email (string, business style; sections: Overview, Context, Action Items)

NEW UPDATE:
{trigger_email}

CONTEXT:
{history_context}
"""
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "text"}},
        )

        content = response.output_text
        parsed = json.loads(content)
        return LLMResult(
            summary=parsed["summary"],
            formatted_email=parsed["formatted_email"],
            key_points=parsed["key_points"],
        )
