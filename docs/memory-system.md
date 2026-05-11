# F.R.I.D.A.Y. Memory System

## Strategy
F.R.I.D.A.Y. uses a dual-layer memory architecture to balance short-term conversational flow with long-term semantic knowledge.

### 1. Short-Term History (SQLite)
- Stores the literal transcript of every session.
- Provides immediate conversational context (sliding window of last 4-8 messages).
- Tables: `sessions`, `messages`.

### 2. Long-Term Semantic Memory (ChromaDB)
- Stores vectorized "facts" extracted from conversation.
- Uses `all-MiniLM-L6-v2` for local embeddings.
- Automatic extraction: Statements like "I am learning Rust" are tagged and stored in the background.
- Retrieval: Cosine-similarity search triggered by recall keywords.

## Extraction Pipeline
- Every user/assistant turn is processed in a background thread.
- Heuristic regex filters identify declarative statements.
- Structured categories: `preference`, `personal`, `learning`, `goal`, `project`.

## Grounding
- Retrieved memories are injected into the LLM system prompt with high-priority markers.
- F.R.I.D.A.Y. is instructed to prioritize these facts over general knowledge.
