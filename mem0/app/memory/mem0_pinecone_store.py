from __future__ import annotations
import os
from typing import List, Dict, Any

# Mem0 (pip package: mem0ai; import module: mem0)
from mem0 import Memory as OSMemory

class Mem0PineconeStore:
    def __init__(self):
        # ---- Embedder settings ----
        # Default to Sentence-Transformers; switch to OpenAI by setting env:
        #   EMBEDDING_PROVIDER=openai
        #   EMBEDDING_MODEL=text-embedding-3-small
        #   EMBEDDING_DIMS=1536  (and set OPENAI_API_KEY)
        embedder_provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
        embedder_model    = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        embedder_dims     = int(os.getenv("EMBEDDING_DIMS", "384"))  # 384 for MiniLM

        # ---- Pinecone settings ----
        pinecone_index     = os.getenv("PINECONE_INDEX", "mem0-chat-memory")
        pinecone_region    = os.getenv("PINECONE_ENV", "us-east-1")
        pinecone_namespace = os.getenv("PINECONE_NAMESPACE", "default")

        # ---- Mem0 config: embedder + Pinecone vector store ----
        config = {
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model":  "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dims": embedder_dims,
                },
            },
            "vector_store": {
                "provider": "pinecone",
                "config": {
                    "collection_name": pinecone_index,
                    "embedding_model_dims": embedder_dims,  # MUST match
                    "namespace": pinecone_namespace,
                    "serverless_config": {
                        "cloud": "aws",
                        "region": pinecone_region,
                    },
                    "metric": "cosine",
                },
            },
        }

        # Mem0 will initialize Pinecone and manage vectors internally
        self.mem0 = OSMemory.from_config(config)

    def add(
        self, *, user_id: str, text: str, mtype: str = "ltm",
        source: str = "chat", tags: List[str] | None = None
    ) -> Dict[str, Any]:
        """
        Store canonical record in Mem0 (with our metadata).
        Mem0 handles embeddings + Pinecone upsert under the hood.
        """
        res = self.mem0.add(
            text,
            user_id=user_id,
            metadata={"type": mtype, "source": source, "tags": (tags or [])},
            infer=False,  # we already summarize/classify; avoid extra LLM work
        )
        mid = res.get("id") or res.get("_id") if isinstance(res, dict) else None
        return {
            "id": mid,
            "metadata": {"user_id": user_id, "type": mtype, "text": text, "source": source, "tags": tags or []},
            "mem0": res,
        }

    def query(self, *, user_id: str, q: str, top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Vector search through Mem0 (uses the Pinecone config).
        Handles both dict and list shapes from Mem0 OSS:
          - {"results": [...]} or {"data": [...]} or {"memories": [...]}
          - or directly a list of items
        Each item can be a dict or a plain string.
        """
        # Correct OSS signature: query is positional, and it uses `limit` (not top_k)
        resp = self.mem0.search(q, user_id=user_id, limit=top_k) or []
    
        # 1) Unwrap container shapes
        if isinstance(resp, dict):
            items = (
                resp.get("results")
                or resp.get("data")
                or resp.get("memories")
                or resp.get("items")
                or []
            )
        else:
            items = resp  # already a list (or list-like)
    
        # 2) Normalize each item
        out: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, dict):
                # try common keys across mem0 variants
                text = (
                    it.get("text")
                    or it.get("value")
                    or it.get("memory")
                    or it.get("content")
                    or ""
                )
                md = it.get("metadata") or it.get("meta") or {}
                # scores can be named differently
                score = it.get("score")
                if score is None:
                    score = it.get("similarity")
                if score is None and "distance" in it:
                    # convert cosine distance to similarity if present
                    try:
                        score = 1.0 - float(it["distance"])
                    except Exception:
                        score = None
            elif isinstance(it, str):
                text, md, score = it, {}, None
            else:
                text, md, score = str(it), {}, None
    
            mtype = md.get("type") if isinstance(md, dict) else None
            out.append({
                "text": text,
                "type": mtype,
                "score": score,
                "metadata": it if isinstance(it, dict) else md,
            })
    
        return out
