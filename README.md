# Mem0 + Pinecone Memory Layer

A small, pragmatic memory layer for chat systems.  
It stores useful facts from conversations, retrieves them when needed, and keeps things tidy (scoring + deduplication).  
UI included (Material UI).

---

## Why this exists

- Chat agents forget things.  
- We only want to store what’s actually useful.  
- We need a simple way to search past facts without sifting through logs.

This project gives you:
- A **memory store** (Mem0) backed by **Pinecone** for fast semantic search.
- A **policy** that decides when to store something (with reasons).
- A **UI** to see what was retrieved, what got stored, and why.

---

## What gets stored (memory types)

We tag every memory with a type. This helps with scoring, retention, and display.

- **factual** – concrete, verifiable info (e.g., “SSE endpoint is `/v1/events` on port 8001”).
- **semantic** – general domain knowledge.
- **episodic** – time-bound events (e.g., “Met with Sam on Sep 10”).
- **preference** – stable user choices (e.g., “prefers short answers”).
- **task_state** – temporary state during ongoing work.
- **procedure** – step-by-step instructions or playbooks.
- **stm** – short-term scratchpad items.
- **ltm** – long-term, durable knowledge.

You can keep them all, rename, or collapse them to a smaller set.

---

## When something gets stored (the policy)

Every turn can produce a **candidate memory**. The policy decides to **store** or **skip** it.

Steps:

1) **Redaction**  
   Remove/obfuscate anything sensitive (tokens, PII) before it goes to storage.

2) **Classification**  
   Assign one of the memory types above.

3) **Scoring**  
   We compute three simple metrics, then blend them into a single score:
   - **Novelty (0–1):** How new is this vs. what we already have?  
     - We embed the candidate and search nearest neighbors.  
     - `novelty = 1 - best_similarity`.
   - **Specificity (0–1):** Is it concrete and actionable?  
     - Names, numbers, endpoints, dates, versions, etc. increase it.
   - **Longevity (0–1):** Will it still matter later?  
     - Facts/procedures/semantic tend to last longer than episodic/task items.

   Final score (defaults):  
   `score = 0.35 * novelty + 0.40 * specificity + 0.25 * longevity`

4) **Dedup**  
   We check top-K neighbors in Pinecone.  
   If `similarity >= 0.90` to something already stored → **skip_duplicate**.  
   (You can merge/refresh instead if you prefer.)

5) **Decision**  
   - `store` if `score >= threshold` **and** not a duplicate  
   - `skip_low_score` if below threshold  
   - `skip_duplicate` if near-duplicate

Each `/chat` call returns a **policy trace** so you can see the type, rationale, scores, and decision.

---

## Retrieval (how the agent “remembers”)

At answer time we:
1) Build a semantic query from the user’s message.
2) Search Mem0 (Pinecone under the hood) scoped to `user_id`.
3) Return top matches with `{ text, type, score }`.
4) The UI shows what was used.

Tip: you can also diversify results (e.g., keep at most one per memory type).

---

## Storage architecture

We configure **Mem0** to manage vectors in **Pinecone**:

- **Embedder:** Hugging Face / Sentence-Transformers  
  Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dims)  
- **Vector DB:** Pinecone (cosine)

Mem0 handles the embeddings + upserts; you only call `add()` and `search()`.

---

## API (what you can call)

### `POST /chat`
**Input:**
```json
{
  "user_id": "adarsh",
  "message": "Remember: our SSE endpoint is /v1/events on port 8001",
  "type": "auto"
}
```

**Output (shape):**
```json
{
  "reply": "…",
  "retrieved": [
    { "text": "…", "type": "factual", "score": 0.91, "metadata": { ... } }
  ],
  "stored": {
    "id": "…",
    "metadata": { "user_id": "adarsh", "type": "factual", "text": "…" }
  },
  "summary": "…",
  "policy": {
    "classified_type": "factual",
    "rationale": "Contains endpoint and port; actionable.",
    "specificity": 0.92,
    "longevity": 0.70,
    "score": 0.83,
    "decision": "store",
    "dedup_top_scores": [0.41, 0.26, 0.18]
  }
}
```

### `GET /memory/retrieve`
Query params: `user_id`, `q`, `top_k`  
Returns: list of `{ text, type, score, metadata }`

---

## Config (env)

**Pinecone**
```
PINECONE_API_KEY=...
PINECONE_INDEX=mem0-chat-memory
PINECONE_ENV=us-east-1
PINECONE_NAMESPACE=default
```

**Embeddings**
```
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMS=384
```
> Pinecone index dimension must match `EMBEDDING_DIMS` (384 here).

**Policy thresholds (tune as needed)**
```
MEM_POLICY_SCORE_MIN=0.60
MEM_POLICY_DEDUP_SIM=0.90
```

(If you also run a chat model behind `/chat`, set its keys/IDs separately—this layer doesn’t depend on them.)

---

## How to run

### Backend
- Start your FastAPI app (e.g., `uvicorn app.main:app --reload --port 8001`).
- Ensure ENV vars are set. First run will create the Pinecone index if missing.

### UI
Material UI app (Create React App):

```bash
cd mem0_ui_cra
npm install
echo REACT_APP_API=http://localhost:8001 > .env
npm start
```

Open http://localhost:3000

You’ll see:
- **Chat** on the left.
- **Retrieved memories** (type chips + scores), **stored item**, and **policy trace** on the right.
- A **Search Memory** panel to test retrieval manually.

---

## Troubleshooting

- **“Unsupported embedding provider”**  
  Use `EMBEDDING_PROVIDER=huggingface` with `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`.

- **Dimension mismatch**  
  Pinecone index dims must match `EMBEDDING_DIMS`.

- **`Memory.search` shape differences**  
  Some versions return `{results:[…]}`; others return a list. Normalize both forms.

- **Duplicates slipping through**  
  Tighten the dedup cutoff (e.g., `0.92`) or merge when similar.

- **Too much stored**  
  Raise `MEM_POLICY_SCORE_MIN`, or make specificity rules stricter.

---

## How to customize

- **Retention:** auto-expire `stm` sooner; keep `ltm` longer.
- **Merging:** merge updated facts instead of skipping near-duplicates.
- **Per-type thresholds:** different score bars per memory type.
- **Search diversity:** cap results per type to avoid repetition.

---

## Mental model (quick recap)

1) **Retrieve** what seems relevant for the current turn.  
2) **Answer**.  
3) **Decide** if anything is worth keeping (classify → score → dedup).  
4) **Store** only if it passes the bar.  
5) **Show your work** (policy trace) to tune with confidence.
