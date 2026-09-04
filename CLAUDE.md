# CLAUDE.md — RAG Technical Assistant

> Architectural context for this project. Read it in full before iterating.
> If you're about to make a decision that contradicts something here, say so explicitly before writing code.

---

## 1. What this is

A conversational assistant that answers questions over a private technical corpus
(documentation, rulebooks, manuals) while **always citing the exact source of every claim it
makes**, and refusing to answer when retrieval isn't good enough.

This is a portfolio project with a specific thesis: **the hard part of RAG isn't prompting, it's
evaluation.** Anyone can wire up a "chat with your PDF" in an afternoon. Almost nobody builds the
harness that catches the moment that chat starts lying.

### Relationship to arbiter-mars

This project is the companion to [`arbiter-mars`](https://github.com/Adriandev0602/arbiter-mars),
and shares its underlying thesis: **strict architectural control over a probabilistic model.**

| | arbiter-mars | this project |
|---|---|---|
| Hard rule | The LLM never does math | The LLM never answers without a source |
| How it's enforced | A graph that routes through `ToolNode` | Retrieval contract + abstention |
| What it demonstrates | Deterministic tool calling | Auditable, evaluated retrieval |

**Recommended starting corpus:** the official Terraforming Mars rulebook plus the community FAQ.
Practical reasons: the domain is already well understood (the golden set can be written without
research), the text is dense with cross-references (genuinely hard RAG, not a toy demo), and it
turns two repos into one portfolio with a coherent point of view instead of two unrelated
projects. Swap in a different corpus if you prefer — nothing else in the design depends on the
domain, only the `corpus/` folder does.

---

## 2. The non-negotiable rule

**Every sentence in an answer that asserts a fact must have a `chunk_id` behind it.**

This isn't a UX preference. It's the property the project exists to demonstrate. It's enforced by
three layers, and all three have to stay standing:

1. **The system prompt** forces the model to emit answers in a structured format where every claim
   is accompanied by the ids of the chunks that back it.
2. **The post-generation validator** (`app/rag/grounding.py`) rejects any answer that cites a
   `chunk_id` not present in the retrieved context. If the model hallucinates a citation, the
   answer doesn't go out — it's retried once, then degraded to abstention.
3. **The abstention threshold**: if the best retrieval score falls below the configured threshold,
   the generator model isn't called at all. The system responds "I couldn't find this in the
   corpus" and lists suggested queries instead.

A plausible answer without a source is a high-severity bug, not a mediocre answer. The system
should say "I don't know" too often rather than make things up too little.

---

## 3. Structure

```
backend/app/
├── rag/
│   ├── chunking.py      # document -> chunks with metadata (source, section, offsets)
│   ├── embed.py         # chunks -> vectors (batched, disk-cached)
│   ├── retrieve.py      # query -> candidate chunks + scores
│   ├── rerank.py        # top-k reordering (optional, see §7)
│   ├── grounding.py     # citation validator — layer 2 of §2
│   └── answer.py        # orchestration: retrieve -> prompt -> generate -> validate
├── llm/
│   ├── base.py          # abstract provider interface (see §5)
│   ├── openai.py
│   ├── anthropic.py
│   └── gemini.py
├── db/
│   └── supabase.py      # THE ONLY layer with persistence I/O
├── api/
│   └── routes.py        # FastAPI: /ingest, /ask, /health
└── evals/
    ├── golden.jsonl     # the reference set (see §6)
    ├── metrics.py       # recall@k, groundedness, abstention rate
    └── run.py           # harness CLI
```

**Boundary rules** (same as in arbiter-mars, and for the same reason):

- Modules in `rag/` are pure functions except `retrieve.py` and `answer.py`. They don't import
  FastAPI or Supabase. They take data in, return data out.
- `chunking.py` doesn't know which embedding model will be used. `embed.py` doesn't know where the
  chunks came from. If you catch yourself passing a global config object between the two, stop and
  redesign.
- All persistence I/O lives in `db/`. If `rag/` needs something from the database, it's passed in
  already resolved.

---

## 4. Retrieval contract

A chunk is an object with this shape, and it doesn't change without updating this document:

```python
{
    "chunk_id": "rulebook__3.2__004",   # <source>__<section>__<index>, stable across re-ingestions
    "text": "...",
    "source": "rulebook.pdf",
    "section": "3.2 Standard Projects",
    "page": 12,
    "token_count": 287,
}
```

The `chunk_id` must be **stable**: re-ingesting the same document with no changes must produce
exactly the same ids. Otherwise the golden set breaks on every run and the evaluation harness
becomes useless. That's why the id is derived from the section rather than a global counter.

**Chunking decisions that need to be documented when made** (write down the *why* in the commit,
not just the *what*):

- Target size and overlap. Start around ~500 tokens with 15% overlap and tune against the golden
  set, not intuition.
- How tables and lists get split. Cutting a table in half is the number-one cause of bad retrieval
  in technical documentation.
- Whether to do *contextual retrieval* (prepending a section summary to each chunk before
  embedding). It's expensive in ingestion tokens and usually worth it. Measure it, don't assume it.

---

## 5. The provider layer

Nothing outside `llm/` may import a concrete provider's SDK. Everything goes through the
`llm/base.py` interface:

```python
class LLMProvider(Protocol):
    def complete(self, messages: list[Message], *, tools: list[Tool] | None = None) -> Completion: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

The provider is selected via an environment variable (`LLM_PROVIDER=openai|anthropic|gemini`) and
the system has to behave identically with all three. **This isn't over-engineering, it's the point
of the exercise:**

- The evaluation harness (§6) runs the same golden set against all three providers and produces a
  comparison table. That's a publishable result for the README, and it's what keeps this from
  being just another demo.
- At a startup, when pricing changes or a new model ships, migrating should cost hours, not weeks.
  Being able to say that in an interview, with the code to back it up, is worth more than a list of
  technologies.

**Watch out for the embeddings trap:** vectors from different providers aren't comparable. The
index is tied to whichever embedding model built it. Store the embedding model's name in the
index's metadata and fail loudly if someone queries with a different model than the one used at
ingestion time.

---

## 6. Evaluation

Without this, the project doesn't exist. It's half the thesis.

**Golden set** — `evals/golden.jsonl`, at least 40 hand-written entries:

```json
{
  "id": "g-018",
  "question": "Can I pay for a standard project with steel?",
  "expected_chunk_ids": ["rulebook__3.2__004"],
  "expected_answer_contains": ["no", "steel", "building cards only"],
  "should_abstain": false
}
```

Deliberately include **at least 8 questions the corpus can't answer**, with `should_abstain: true`.
A system that never abstains is lying, and the golden set needs to be able to prove it.

**Metrics reported by `evals/run.py`:**

| Metric | What it measures | Minimum threshold |
|---|---|---|
| `recall@5` | Is the correct chunk among the top 5 retrieved? | ≥ 0.85 |
| `groundedness` | % of claims with a valid citation to the corpus | 1.00 — no exceptions |
| `abstention_precision` | Of the times it abstained, how many were warranted? | ≥ 0.90 |
| `answer_match` | % containing the expected terms | ≥ 0.75 |

`groundedness` is the only one that admits no regression. The others are negotiable against data.

**Working rule:** every change to chunking, prompts, or retrieval parameters ships with a harness
run in the same commit. If a metric drops, the commit message explains why the trade-off is worth
it. No run, no merge.

---

## 7. Deliberately out of scope

Writing this down matters as much as what's inside: a scope that's never closed never ships.

- **Multi-tenancy and user accounts.** One corpus, one index.
- **Real-time ingestion.** Ingestion is a command run by hand.
- **Fine-tuning.** Everything is retrieval plus prompting.
- **Reranking with a dedicated model** (`rerank.py`) stays a *stretch goal*. Only build it if the
  harness shows `recall@5` is fine but the final answer is still wrong — that's the specific
  symptom reranking fixes. Otherwise it's complexity without a cause.
- **Token streaming to the frontend.** Nice to have, doesn't prove anything new. Only if there's
  time left at the end.

---

## 8. Build order

Don't start with the frontend. Each milestone has to be verifiable before moving to the next.

1. **Ingestion and chunking.** Corpus in `corpus/` -> chunks in Supabase with stable ids.
   Verifiable: re-ingesting twice produces identical ids.
2. **Embeddings and index.** Pinecone populated, with the embedding model saved in metadata.
   Verifiable: a manual query returns visibly relevant chunks.
3. **Golden set.** The 40 entries, written before touching generation. Writing them afterward means
   writing them to pass.
4. **Evaluation harness** measuring `recall@k` only. Chunking can now be optimized against data.
5. **Generation with citations** plus the grounding validator. This is where it becomes the
   project.
6. **Abstention** and the rest of the metrics.
7. **FastAPI** with `/ingest`, `/ask`, `/health`.
8. **Provider comparison**: all three, same golden set, table in the README.
9. **Minimal frontend.** A text box and clickable citations. Nothing more.
10. **Deploy** on Vercel plus Supabase, with the harness run in CI.

An honest README at step 5 is worth more than a polished product without step 3.

---

## 9. Conventions

- **Tests alongside every module.** `rag/` modules are pure functions: there's no excuse not to
  cover them. arbiter-mars set the bar at 533 tests; don't go below that in proportion.
- **No `except: pass`.** If a provider call fails, it propagates with context about which query
  caused it.
- **Keys only via environment.** `.env.example` is versioned, `.env` never is.
- **Commits in the imperative**, describing the why. `tune chunking to 400 tokens: recall@5 goes
  0.81 → 0.89` is useful; `fix chunking` isn't.
- **This document gets updated when a design decision changes**, in the same commit. A stale
  design doc is worse than none.
- Keep an `AGENTS.md` as a tool-agnostic copy, same as in arbiter-mars.

---

## 10. Definition of done

The project is done when **all** of this is true:

- [ ] The harness runs with one command and reports all four metrics.
- [ ] `groundedness` is 1.00 across the full golden set.
- [ ] The system correctly abstains on all 8 unanswerable questions.
- [ ] The same golden set has run against all three providers and the table is in the README.
- [ ] It's deployed and there's a URL someone can open.
- [ ] The README explains the thesis in the first two paragraphs, with real numbers.

Once all six are checked — **and not before** — this block gets added to the resume, with the
brackets replaced by the actual numbers:

> **RAG Technical Assistant** — *Python · FastAPI · Pinecone · Supabase · Vercel*
> - Built a retrieval assistant that cites a source for every claim and abstains when retrieval
>   confidence is insufficient, validated by a post-generation grounding check that rejects any
>   answer citing a chunk outside the retrieved context.
> - Wrote a [40]-question golden set and an evaluation harness measuring recall@5, groundedness and
>   abstention precision; drove recall@5 from [x] to [y] by tuning chunking against the harness
>   rather than by intuition.
> - Built the LLM layer provider-agnostic and benchmarked the same golden set across OpenAI,
>   Anthropic and Gemini, publishing the comparison — swapping providers is a config change.
> - Shipped the whole thing solo on Vercel and Supabase with the eval harness running in CI.

Until it exists, it doesn't go on the resume.
