# app/llm/groq_client.py
from __future__ import annotations
import os
from typing import Optional

from langchain_aws import ChatBedrock
from langchain.schema import SystemMessage, HumanMessage

class GroqClient:
    """
    Drop-in Bedrock client with the same interface used elsewhere:
      - chat(system: str, user: str, temperature: float = 0.3) -> str
      - summarize(content: str, max_chars: int = 320) -> str

    Env vars:
      BEDROCK_MODEL_ID   e.g. "anthropic.claude-3-5-sonnet-20240620-v1:0"
                         or   "meta.llama3-70b-instruct-v1:0"
                         or   "amazon.titan-text-lite-v1"
      BEDROCK_REGION     e.g. "us-east-1" (defaults to AWS_REGION or us-east-1)
      BEDROCK_TEMPERATURE (optional default temperature)
      BEDROCK_MAX_TOKENS  (optional default max tokens)
    AWS creds are taken from the standard SDK chain (env/instance role/profile).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,   # ignored; kept for signature compatibility
        model: Optional[str] = None
    ):
        # Keep the same env var name your app used before, but allow override:
        self.model_id = model or os.getenv(
            "BEDROCK_MODEL_ID",
            # sensible default: Claude 3.5 Sonnet (adjust if your account lacks access)
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        # Region precedence: explicit var > AWS_REGION > default
        self.region = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")

        # Defaults (can be overridden per-call)
        self.default_temperature = float(os.getenv("BEDROCK_TEMPERATURE", "0.3"))
        self.default_max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", "2048"))

        # Create the Bedrock chat model via langchain_aws
        # model_kwargs are provider-specific but LangChain normalizes common params
        self.llm = ChatBedrock(
            model_id=self.model_id,
            region_name=self.region,
            # You can pass global defaults here; still override per-call below
            model_kwargs={}
        )

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        # Use call-time temperature if provided, else default
        temp = temperature if temperature is not None else self.default_temperature

        # Compose messages (system + user) to preserve your original signature
        messages = [
            SystemMessage(content=system or ""),
            HumanMessage(content=user or "")
        ]

        # Most Bedrock providers accept max_tokens/temperature via kwargs; LC handles mapping
        resp = self.llm.invoke(
            messages,
            temperature=temp,
            max_tokens=self.default_max_tokens,
        )
        # LangChain returns a ChatMessage; text is in .content
        return (resp.content or "").strip()

    def summarize(self, content: str, max_chars: int = 320) -> str:
        system = (
            "You are a precise summarizer. Return a crisp, self-contained summary "
            "within the character limit."
        )
        user = f"Summarize within {max_chars} characters:\n\n{content}"
        return self.chat(system, user, temperature=0.2)
