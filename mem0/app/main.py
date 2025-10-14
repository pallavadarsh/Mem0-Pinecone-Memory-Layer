
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.schemas import ChatRequest, ChatResponse, RetrieveResponse
from app.memory.mem0_pinecone_store import Mem0PineconeStore
from app.llm.groq_client import GroqClient
from app.policy import PolicyConfig, redact, classify_llm, specificity, longevity, final_score, is_duplicate_from_matches

app = FastAPI(title="Mem0 + Pinecone (LLM classify, dedup, summarize)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = Mem0PineconeStore()
llm = GroqClient()
cfg = PolicyConfig()

SYSTEM_PROMPT = "You are a helpful assistant. Use retrieved notes if relevant and be concise."

def build_prompt(user_msg: str, memories: list[dict]) -> str:
    mem_lines = "\n".join(f"- ({m.get('type')}) {m.get('text')}" for m in memories)
    return f"""System: {SYSTEM_PROMPT}
User: {user_msg}

Relevant memory (if any):
{mem_lines}

Answer:
"""

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1) retrieve for context
    retrieved = store.query(user_id=req.user_id, q=req.message, top_k=6)

    # 2) LLM answer
    prompt = build_prompt(req.message, retrieved)
    try:
        reply = llm.chat(system=SYSTEM_PROMPT, user=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq chat failed: {e}")

    # Candidate memory (redacted)
    candidate = f"Q: {req.message}\nA: {reply}"
    red, _ = redact(candidate)

    # 3) Classify via LLM (override with req.type unless 'auto')
    mtype, rationale = classify_llm(llm, red, req.type)

    # 4) Score
    spec = specificity(red)
    longv = longevity(red, mtype)
    novelty = 0.7
    score = final_score(novelty, spec, longv)

    # 5) Dedup via Pinecone
    dedup_matches = store.query(user_id=req.user_id, q=red, top_k=3)
    is_dup = is_duplicate_from_matches(dedup_matches, cfg.dedup_sim_threshold)

    stored = None
    summary = None
    if (not is_dup) and (score >= cfg.decision_threshold):
        try:
            summary = llm.summarize(candidate, max_chars=320)
            stored = store.add(user_id=req.user_id, text=summary, mtype=mtype, source="chat", tags=req.tags or [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Store failed: {e}")

    memory_log = {
        "classified_type": mtype,
        "rationale": rationale,
        "specificity": round(spec, 3),
        "longevity": round(longv, 3),
        "score": round(score, 3),
        "decision": "store" if stored else ("skip_duplicate" if is_dup else "skip_low_score"),
        "dedup_top_scores": [m.get("score") for m in dedup_matches],
    }

    return ChatResponse(
        reply=reply,
        retrieved=retrieved,
        stored=stored,
        summary=summary,
        policy=memory_log,   # <— NEW
    )


@app.get("/memory/retrieve", response_model=RetrieveResponse)
def memory_retrieve(user_id: str, q: str, top_k: int = 8):
    results = store.query(user_id=user_id, q=q, top_k=top_k)
    return RetrieveResponse(results=results or [])
