"""FastAPI app exposing /ingest, /ask, and /health."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="rag-technical-assistant")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest")
def ingest() -> dict:
    raise NotImplementedError


@app.post("/ask")
def ask() -> dict:
    raise NotImplementedError
