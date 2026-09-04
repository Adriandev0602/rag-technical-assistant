# rag-technical-assistant

Asistente conversacional que responde preguntas sobre un corpus técnico privado citando siempre
la fuente exacta de donde sacó cada afirmación, y que se abstiene cuando la recuperación no
alcanza. El proyecto no es "un chat con tu PDF" — es el arnés de evaluación que demuestra cuándo
ese chat empieza a mentir.

Complemento de [`arbiter-mars`](https://github.com/Adriandev0602/arbiter-mars): mismo principio de
control arquitectónico estricto sobre un modelo probabilístico, aplicado acá a recuperación
auditable en lugar de tool calling determinista.

Ver `CLAUDE.md` para el diseño completo: contrato de recuperación, capa de proveedores, arnés de
evaluación, y orden de construcción.

## Estado

Esqueleto inicial. Ver checklist de "Definition of done" en `CLAUDE.md` §10.

## Estructura

```
backend/app/
├── rag/        # chunking, embeddings, retrieval, grounding, orquestación — funciones puras
├── llm/        # interfaz de proveedor (OpenAI / Anthropic / Gemini)
├── db/         # única capa con I/O de persistencia (Supabase)
├── api/        # FastAPI: /ingest, /ask, /health
└── evals/      # golden set + arnés de métricas
corpus/         # documentos fuente
```

## Desarrollo

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # completar claves
```
