# Document Assistant

Upload PDFs, ask questions about them, and get grounded, cited answers — built with a real multi-tenant backend so different clients' documents stay isolated from each other.

Built as a follow-on to [GitHub Trust Checker](../trust-checker), reusing the same core RAG pattern (chunk → embed → retrieve → cite) but adapted for a genuinely different, harder domain: binary PDF ingestion instead of API-fetched markdown, multi-document search, and real multi-tenant data isolation via Postgres + pgvector.

## What it does

- Upload one or more PDFs via a real file-upload API
- Ask natural-language questions; answers are generated only from retrieved, relevant chunks and cite the source filename + page number
- Every document is owned by a specific client (identified by an API key); one client can never search or see another client's documents
- Re-uploading an identical file is detected via content hashing and skipped, both in the database and on disk
- Malicious content — in either an uploaded document or a user's question — is screened for prompt-injection patterns before it ever reaches the LLM

## Architecture

```
React frontend (API key → upload → chat)
        │
        ▼
FastAPI  /upload  and  /ask
        │
        ├─ X-API-Key header → resolved to client_id (FastAPI dependency)
        │
   /upload:
        ├─ save file → guardrail-check extracted text → dedup-check by content hash
        └─ chunk → embed → insert into Postgres (clients → documents → chunks)
        │
   /ask:
        ├─ verify every requested document is owned by this client (SQL join)
        ├─ guardrail-check the question
        ├─ embed question → pgvector cosine-distance search, scoped by client_id,
        │  filtered by a max-distance relevance ceiling
        └─ build prompt from retrieved chunks → Claude → cited answer
```

## Tech stack

- **Ingestion:** `pdfplumber` (PDF text extraction, page-tracked)
- **Chunking:** fixed-size sliding window with overlap (no natural headers to split on, unlike markdown)
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim)
- **Storage & retrieval:** PostgreSQL + `pgvector` extension — one database for both ownership/relational data and vector similarity search
- **LLM:** Claude (Anthropic API), grounded strictly to retrieved context
- **Backend:** FastAPI
- **Frontend:** React + Vite + Tailwind

## Why Postgres + pgvector instead of a separate vector DB

The original design (borrowed from the trust checker) used Qdrant, with collections named by filename. That has a real flaw: two different clients uploading a same-named file could collide into the same collection and leak data into each other's search results. A dedicated vector database has no native concept of "ownership."

Postgres does. Migrating to `pgvector` means ownership (`clients` → `documents` → `chunks`, enforced by foreign keys) and similarity search (the `embedding <=> query` operator) live in the same system — a client's access boundary is enforced structurally, by a SQL `JOIN`, not by naming convention or an easily-bypassed application-level check.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

Create `.env` in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

Start Postgres + pgvector (via Docker):
```bash
docker run --name doc-assistant-db -e POSTGRES_PASSWORD=devpassword -p 5432:5432 -d pgvector/pgvector:pg16
docker exec -i doc-assistant-db psql -U postgres < backend/schema.sql
```

Create a test client (needed to get an API key):
```bash
python -c "from backend.db import insert_client; print(insert_client('Test Client', 'your-test-key'))"
```

Run the API:
```bash
uvicorn backend.api:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL, paste your API key, upload a PDF, and start asking questions.

## Known limitations

- **Retrieval has no reranking step** — single-stage cosine-distance search with a fixed relevance ceiling (`max_distance`), no cross-encoder reranking on top.
- **Guardrails are keyword-based**, not semantic — they can be evaded by rephrasing, and can false-positive on legitimate text that happens to quote a flagged phrase (discussed at length in the companion issues-and-resolutions writeup).
- **No conversation memory** — each `/ask` request is fully independent; a future multi-turn UI would need to manage and resend prior context itself.
- **Not yet deployed** — runs locally against a Dockerized Postgres instance; a real deployment would point at a managed Postgres/pgvector provider (e.g. Supabase, Neon) instead.
- **API key auth only** — no password/account system, no key rotation or expiry; adequate for a local/demo setting, not production-grade auth.

## Related

A parallel, detailed log of every real bug hit while building this project (and the trust checker) — what broke, why, and how it was diagnosed — is documented separately in `issues_and_resolutions.pdf`.