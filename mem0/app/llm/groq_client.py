import requests, os

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is missing")

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        payload = {"model": self.model, "messages": [
            {"role":"system","content":system},
            {"role":"user","content":user}
        ], "temperature": temperature}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()

    def summarize(self, content: str, max_chars: int = 320) -> str:
        system = "You are a precise summarizer. Return a crisp, self-contained summary within the character limit."
        user = f"Summarize within {max_chars} characters:\n\n{content}"
        return self.chat(system, user, temperature=0.2)