custom_fact_extraction_prompt = """
You are a memory extractor for an AI agent.

For each input text, you must:
1. Decide if there is anything worth storing as long-term memory.
2. For each such piece, classify it as EXACTLY ONE of:
   - factual: stable facts, preferences, account details, domain facts.
   - episodic: specific events or experiences tied to time or context.
   - semantic: general knowledge, skills, or relationships between concepts.

Return JSON with a single key "facts".
"facts" must be an array of strings.
Each string MUST follow this exact format:

<MEMORY_TYPE>|<MEMORY_TEXT>

Where:
- MEMORY_TYPE is one of: factual, episodic, semantic
- MEMORY_TEXT is a short, self-contained sentence.

Examples:

Input: "My name is Adarsh and I live in Bangalore."
Output: {"facts": ["factual|User's name is Adarsh", "factual|User lives in Bangalore"]}

Input: "Yesterday I deployed a new Mem0-based memory layer for my RAG app."
Output: {"facts": ["episodic|Yesterday the user deployed a new Mem0-based memory layer for their RAG app"]}

Input: "I usually work with FastAPI, LangGraph, and Pinecone."
Output: {"facts": ["semantic|User works with FastAPI, LangGraph, and Pinecone"]}

If there is nothing worth storing, return:
{"facts": []}
"""




custom_update_memory_prompt = """
You are a memory manager for an AI assistant that supports business workflows.

You will receive:
- existing_memories: JSON array of objects with fields:
  - "id": string
  - "text": string
- new_facts: JSON array of strings.
  Each string is in the format:
    "<MEMORY_TYPE>|<MEMORY_TEXT>"
  where MEMORY_TYPE is one of:
    - factual
    - semantic
    - episodic

Definitions:
- factual: Stable, objective information about a person, company, account, or system.
  Examples: job titles, locations, contract values, product SKUs, plan types.
- episodic: Specific events or interactions tied to a date, time, or context.
  Examples: meetings, calls, incidents, deployments, renewals.
- semantic: General knowledge, preferences, policies, or patterns.
  Examples: "customer prefers email communication", "team uses agile methodology".

Your job:
For each item in new_facts, compare it against existing_memories and decide:
- ADD:     Create a new memory because the fact is new and not covered.
- UPDATE:  Update an existing memory because the fact changes or refines it.
- DELETE:  Remove an existing memory because the fact contradicts or invalidates it.
- NONE:    Do nothing because the fact is already captured or is not useful to store.

Rules of thumb:
- Factual memories (profile, account data, plan details) should usually UPDATE or DELETE old conflicting facts
  rather than adding duplicates. Example: if "Customer is on Basic plan" exists and a new fact says
  "Customer upgraded to Enterprise plan", you should UPDATE the plan memory.
- Episodic memories (specific meetings, incidents, transactions) are usually ADD, unless the new fact corrects a
  clearly inaccurate event.
- Semantic memories (preferences, working styles, general policies) may UPDATE when they evolve over time,
  otherwise ADD if genuinely new.

Output JSON with a top-level key "memory" whose value is an array.
Each item in "memory" MUST have exactly these fields:
- "id": string (existing id for UPDATE/DELETE/NONE, new id like "new_0", "new_1" for ADD)
- "text": string (for ADD and UPDATE; can be empty "" for DELETE or NONE)
- "event": one of "ADD", "UPDATE", "DELETE", "NONE"
- "old_memory": string (only for UPDATE; empty string otherwise)
- "memory_type": one of "factual", "semantic", "episodic"

Important:
- When you choose UPDATE, reuse the existing memory "id" and include its original text as "old_memory".
- For DELETE, keep the original "id" and set "text" to "".
- For NONE, keep the original "id" and set "text" to "".
- For ADD, generate a new id like "new_0", "new_1", etc.

Business examples:

Example 1: Account upgrade

existing_memories:
[
  {"id": "m1", "text": "Customer ACME Corp is on the Basic subscription plan"},
  {"id": "m2", "text": "ACME Corp prefers quarterly business reviews via Zoom"}
]

new_facts:
[
  "factual|ACME Corp upgraded to the Enterprise subscription plan"
]

Reasonable output:

{
  "memory": [
    {
      "id": "m1",
      "text": "Customer ACME Corp is on the Enterprise subscription plan",
      "event": "UPDATE",
      "old_memory": "Customer ACME Corp is on the Basic subscription plan",
      "memory_type": "factual"
    }
  ]
}

Example 2: Communication preference change + new meeting

existing_memories:
[
  {"id": "m3", "text": "Contact Sarah prefers email communication"},
  {"id": "m4", "text": "Last quarterly review with Contoso was held in January 2025"}
]

new_facts:
[
  "semantic|Sarah now prefers to be contacted via Microsoft Teams",
  "episodic|On 10 March 2025, we had a renewal planning call with Contoso"
]

Reasonable output:

{
  "memory": [
    {
      "id": "m3",
      "text": "Contact Sarah prefers communication via Microsoft Teams",
      "event": "UPDATE",
      "old_memory": "Contact Sarah prefers email communication",
      "memory_type": "semantic"
    },
    {
      "id": "new_0",
      "text": "On 10 March 2025, we had a renewal planning call with Contoso",
      "event": "ADD",
      "old_memory": "",
      "memory_type": "episodic"
    }
  ]
}

Now decide the actions for the given existing_memories and new_facts.
Return ONLY the JSON object.
"""
