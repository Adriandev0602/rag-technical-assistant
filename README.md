# RAG Technical Assistant

A retrieval-augmented assistant that answers questions over a private technical corpus (rulebooks,
manuals, internal docs) while citing the exact source behind every claim it makes — and refusing
to answer when retrieval confidence isn't high enough.

The premise here is that building a "chat with your PDF" demo is easy; building the harness that
catches the moment it starts making things up is not. Most RAG projects fail silently: retrieval
quietly degrades, the model fills the gap with a plausible-sounding guess, and nobody notices until
a user acts on wrong information. This project treats that failure mode as the actual engineering
problem, not an edge case to patch later.

Companion project to [`arbiter-mars`](https://github.com/Adriandev0602/arbiter-mars), which applies
the same philosophy — strict architectural guardrails around a probabilistic model — to
deterministic tool-calling instead of retrieval.

## Why this approach

Three enforcement layers, all mandatory, none optional:

1. **Structured citations at generation time.** The model is required to emit answers where every
   factual sentence is tied to specific chunk ids, not free-form prose with sources bolted on
   after the fact.
2. **A post-generation grounding validator.** Every cited chunk id is checked against what was
   actually retrieved. If the model cites something it wasn't given, the answer is rejected,
   retried once, and if it still fails, the system abstains instead of shipping a hallucinated
   citation.
3. **A hard abstention threshold.** When the best retrieval score falls below a configured
   threshold, the generator is never even called — no context, no generation, no risk. The system
   says "I couldn't find this in the corpus" and suggests alternative queries.

A confident wrong answer is treated as a severity-1 bug. A system that says "I don't know" too
often is preferable to one that invents an answer too rarely.

## What actually gets measured

The evaluation harness runs a hand-written golden set (40+ question/answer pairs, at least 8 of
which are intentionally unanswerable from the corpus) and reports:

| Metric | What it measures | Target |
|---|---|---|
| `recall@5` | Is the correct chunk among the top 5 retrieved? | ≥ 0.85 |
| `groundedness` | % of claims backed by a valid citation | 1.00 — no exceptions |
| `abstention_precision` | Of the times the system abstained, how many were warranted? | ≥ 0.90 |
| `answer_match` | % of answers containing the expected terms | ≥ 0.75 |

`groundedness` is non-negotiable — it's the property the whole system exists to guarantee. The
other three are tuned against data, not intuition: every change to chunking, prompting, or
retrieval parameters is validated with a harness run before it ships, and any regression has to be
justified in the commit that introduces it.

The provider layer is deliberately abstracted behind a single interface (OpenAI, Anthropic,
Gemini) so the same golden set can be benchmarked across all three and swapping providers is a
config change, not a rewrite — a comparison table across providers is a first-class output of this
project, not an afterthought.

## Architecture

```
backend/app/
├── rag/
│   ├── chunking.py    # document -> chunks with stable, reproducible ids
│   ├── embed.py       # chunks -> vectors, batched and cached
│   ├── retrieve.py    # query -> candidate chunks + similarity scores
│   ├── rerank.py       # optional top-k reordering (stretch goal, only if data justifies it)
│   ├── grounding.py   # rejects any answer citing a chunk outside the retrieved context
│   └── answer.py      # retrieve -> prompt -> generate -> validate -> abstain-or-answer
├── llm/                # provider-agnostic interface (OpenAI / Anthropic / Gemini)
├── db/                 # the only layer that touches persistence (Supabase)
├── api/                # FastAPI: /ingest, /ask, /health
└── evals/              # golden set + metrics + harness CLI
corpus/                 # source documents
```

Design constraints that shape the code:

- Everything in `rag/` besides `retrieve.py` and `answer.py` is a pure function — no framework
  imports, no hidden I/O, no shared mutable config passed around.
- Chunk ids are derived deterministically from `<source>__<section>__<index>`, so re-ingesting an
  unchanged document produces identical ids — otherwise the golden set breaks on every run.
- Embedding vectors from different providers are never mixed: the index records which embedding
  model built it and fails loudly on a mismatch, rather than silently returning garbage similarity
  scores.

## Explicitly out of scope

- Multi-tenancy — one corpus, one index.
- Real-time ingestion — ingestion is a manual command.
- Fine-tuning — this is retrieval and prompting only.
- Dedicated reranking model — only worth adding if the harness shows good recall but bad final
  answers, which is the specific symptom reranking fixes.
- Token streaming to the frontend — nice, but doesn't demonstrate anything new.

## Status

Initial skeleton. See the roadmap below for what's implemented vs. pending.

- [ ] Ingestion and chunking with stable ids
- [ ] Embeddings + vector index
- [ ] 40+ question golden set
- [ ] Evaluation harness (recall@k)
- [ ] Generation with citations + grounding validator
- [ ] Abstention + full metric suite
- [ ] FastAPI endpoints
- [ ] Cross-provider comparison table
- [ ] Minimal frontend
- [ ] Deployment with harness running in CI

## Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
pytest                # run the test suite
```
