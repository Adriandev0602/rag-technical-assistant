# CLAUDE.md — Asistente Técnico con RAG

> Contexto arquitectónico del proyecto. Leelo completo antes de iterar.
> Si vas a tomar una decisión que contradiga algo de acá, decilo explícitamente antes de escribir código.

---

## 1. Qué es esto

Un asistente conversacional que responde preguntas sobre un corpus técnico privado
(documentación, reglamentos, manuales) **citando siempre la fuente exacta de donde sacó cada
afirmación**, y que se niega a responder cuando la recuperación no alcanza.

Es un proyecto de portfolio y su tesis es específica: **el problema de RAG no es de prompting, es
de evaluación.** Cualquiera arma un "chat con tu PDF" en una tarde. Lo que casi nadie arma es el
arnés que detecta cuándo ese chat empezó a mentir.

### Relación con arbiter-mars

Este proyecto es el complemento de [`arbiter-mars`](https://github.com/Adriandev0602/arbiter-mars),
y comparte su tesis de fondo: **control arquitectónico estricto sobre un modelo probabilístico.**

| | arbiter-mars | este proyecto |
|---|---|---|
| Regla dura | El LLM nunca hace matemática | El LLM nunca responde sin fuente |
| Cómo se garantiza | Grafo que enruta por `ToolNode` | Contrato de recuperación + abstención |
| Qué demuestra | Tool calling determinista | Recuperación auditable y evaluada |

**Corpus recomendado para arrancar:** el reglamento oficial de Terraforming Mars más el FAQ de la
comunidad. Razones prácticas: ya conocés el dominio a fondo (podés escribir el golden set sin
investigar), es texto denso con referencias cruzadas (RAG genuinamente difícil, no un demo de
juguete), y deja los dos proyectos como un portfolio con un punto de vista en vez de dos repos
sueltos. Si preferís otro corpus, cambiá solo la carpeta `corpus/` — nada más del diseño depende
del dominio.

---

## 2. La regla no negociable

**Toda oración de la respuesta que afirme un hecho tiene que tener un `chunk_id` detrás.**

Esto no es una preferencia de UX. Es la propiedad que el proyecto existe para demostrar. Se sostiene
en tres capas, y las tres tienen que seguir en pie:

1. **El system prompt** obliga al modelo a emitir respuestas en un formato estructurado donde cada
   afirmación viene acompañada de los ids de los chunks que la respaldan.
2. **El validador post-generación** (`app/rag/grounding.py`) rechaza toda respuesta que cite un
   `chunk_id` que no está en el contexto recuperado. Si el modelo alucina una cita, la respuesta no
   sale — se reintenta una vez y después se degrada a abstención.
3. **El umbral de abstención**: si el mejor score de recuperación queda por debajo del umbral
   configurado, no se llama al modelo generador en absoluto. Se responde "no encontré esto en el
   corpus" y se listan las consultas sugeridas.

Una respuesta plausible sin fuente es un bug de severidad alta, no una respuesta mediocre.
Prefiero que el sistema diga "no sé" de más a que invente de menos.

---

## 3. Estructura

```
backend/app/
├── rag/
│   ├── chunking.py      # documento → chunks con metadata (fuente, sección, offsets)
│   ├── embed.py         # chunks → vectores (batch, con caché en disco)
│   ├── retrieve.py      # consulta → chunks candidatos + scores
│   ├── rerank.py        # reordenamiento del top-k (opcional, ver §7)
│   ├── grounding.py     # validador de citas — la capa 2 de §2
│   └── answer.py        # orquestación: retrieve → prompt → generar → validar
├── llm/
│   ├── base.py          # interfaz abstracta del proveedor (ver §5)
│   ├── openai.py
│   ├── anthropic.py
│   └── gemini.py
├── db/
│   └── supabase.py      # ÚNICA capa con I/O de persistencia
├── api/
│   └── routes.py        # FastAPI: /ingest, /ask, /health
└── evals/
    ├── golden.jsonl     # el set de referencia (ver §6)
    ├── metrics.py       # recall@k, groundedness, tasa de abstención
    └── run.py           # CLI del arnés
```

**Reglas de frontera** (mismas que en arbiter-mars, y por la misma razón):

- Los módulos de `rag/` son funciones puras salvo `retrieve.py` y `answer.py`. No importan FastAPI
  ni Supabase. Reciben datos, devuelven datos.
- `chunking.py` no sabe qué modelo de embeddings se va a usar. `embed.py` no sabe de dónde salieron
  los chunks. Si te encontrás pasando un objeto de configuración global entre los dos, parás y lo
  rediseñás.
- Todo I/O de persistencia vive en `db/`. Si `rag/` necesita algo de la base, se lo pasan como
  argumento ya resuelto.

---

## 4. Contrato de recuperación

Un chunk es un objeto con esta forma, y esto no cambia sin actualizar este documento:

```python
{
    "chunk_id": "rulebook__3.2__004",   # <fuente>__<sección>__<índice>, estable entre reingestas
    "text": "...",
    "source": "rulebook.pdf",
    "section": "3.2 Standard Projects",
    "page": 12,
    "token_count": 287,
}
```

El `chunk_id` tiene que ser **estable**: reingestar el mismo documento sin cambios produce
exactamente los mismos ids. Si no, el golden set se rompe en cada corrida y el arnés de evaluación
no sirve para nada. Esa es la razón de que el id derive de la sección y no de un contador global.

**Decisiones de chunking que hay que documentar cuando se tomen** (escribí el porqué en el commit,
no solo el qué):

- Tamaño objetivo y solapamiento. Empezá en ~500 tokens con 15% de solapamiento y ajustá contra el
  golden set, no contra la intuición.
- Cómo se cortan las tablas y las listas. Cortar una tabla al medio es la causa número uno de
  recuperación mala en documentación técnica.
- Si se hace *contextual retrieval* (prependear un resumen de la sección a cada chunk antes de
  embeber). Es caro en tokens de ingesta y suele valer la pena. Medilo, no lo asumas.

---

## 5. La capa de proveedores

Nada fuera de `llm/` puede importar el SDK de un proveedor concreto. Todo pasa por la interfaz de
`llm/base.py`:

```python
class LLMProvider(Protocol):
    def complete(self, messages: list[Message], *, tools: list[Tool] | None = None) -> Completion: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

El proveedor se elige por variable de entorno (`LLM_PROVIDER=openai|anthropic|gemini`) y el sistema
tiene que funcionar igual con los tres. **Esto no es sobre-ingeniería, es el punto del ejercicio**:

- El arnés de evaluación (§6) corre el mismo golden set contra los tres proveedores y produce una
  tabla comparativa. Ese es un resultado publicable en el README y es lo que hace que el proyecto no
  sea un demo más.
- En una startup, cuando cambia el precio o sale un modelo nuevo, migrar tiene que costar horas y no
  semanas. Poder decir eso en una entrevista, con el código detrás, vale más que una lista de
  tecnologías.

**Ojo con la trampa de los embeddings:** los vectores de proveedores distintos no son comparables.
El índice queda atado al modelo de embeddings que lo construyó. Guardá el nombre del modelo en la
metadata del índice y fallá ruidosamente si alguien consulta con un modelo distinto al de ingesta.

---

## 6. Evaluación

Sin esto el proyecto no existe. Es la mitad de la tesis.

**Golden set** — `evals/golden.jsonl`, mínimo 40 entradas escritas a mano:

```json
{
  "id": "g-018",
  "question": "¿Puedo pagar un proyecto estándar con acero?",
  "expected_chunk_ids": ["rulebook__3.2__004"],
  "expected_answer_contains": ["no", "acero", "solo cartas de construcción"],
  "should_abstain": false
}
```

Incluí a propósito **al menos 8 preguntas que el corpus no puede responder**, con
`should_abstain: true`. Un sistema que nunca se abstiene está mintiendo y el golden set tiene que
poder demostrarlo.

**Métricas que reporta `evals/run.py`:**

| Métrica | Qué mide | Umbral mínimo |
|---|---|---|
| `recall@5` | ¿el chunk correcto está entre los 5 recuperados? | ≥ 0.85 |
| `groundedness` | % de afirmaciones con cita válida al corpus | 1.00 — sin excepciones |
| `abstention_precision` | de las veces que se abstuvo, ¿cuántas correspondía? | ≥ 0.90 |
| `answer_match` | % que contiene los términos esperados | ≥ 0.75 |

`groundedness` es la única que no admite regresión. Las otras se negocian con datos.

**Regla de trabajo:** cada cambio en chunking, prompts o parámetros de recuperación se acompaña de
una corrida del arnés en el commit. Si una métrica baja, el mensaje del commit explica por qué el
trade-off vale la pena. Sin corrida, no entra.

---

## 7. Fuera de alcance, a propósito

Escribir esto importa tanto como lo de adentro: un alcance que no está cerrado no se termina nunca.

- **Multi-tenancy y cuentas de usuario.** Un corpus, un índice.
- **Ingesta en tiempo real.** La ingesta es un comando que se corre a mano.
- **Fine-tuning.** Todo es recuperación más prompting.
- **Reranking con modelo dedicado** (`rerank.py`) queda como *stretch goal*. Armalo solo si el
  arnés muestra que `recall@5` está bien pero la respuesta igual sale mal — que es el síntoma
  específico que el reranking arregla. Si no, es complejidad sin causa.
- **Streaming de tokens al frontend.** Está bueno, no demuestra nada nuevo. Al final si sobra tiempo.

---

## 8. Orden de construcción

No arranques por el frontend. Cada hito tiene que quedar verificable antes de pasar al siguiente.

1. **Ingesta y chunking.** Corpus en `corpus/` → chunks en Supabase con ids estables. Verificable:
   reingestar dos veces produce ids idénticos.
2. **Embeddings e índice.** Pinecone poblado, con el modelo de embeddings guardado en metadata.
   Verificable: una consulta a mano devuelve chunks visiblemente relevantes.
3. **Golden set.** Las 40 entradas, escritas antes de tocar la generación. Escribirlas después es
   escribirlas para que pasen.
4. **Arnés de evaluación** midiendo solo `recall@k`. Ya podés optimizar chunking con datos.
5. **Generación con citas** más el validador de grounding. Acá se vuelve el proyecto.
6. **Abstención** y el resto de las métricas.
7. **API de FastAPI** con `/ingest`, `/ask`, `/health`.
8. **Comparativa de proveedores**: los tres, mismo golden set, tabla al README.
9. **Frontend mínimo.** Una caja de texto y las citas clickeables. Nada más.
10. **Deploy** en Vercel más Supabase, con la corrida del arnés en CI.

Un README honesto en el paso 5 vale más que un producto pulido sin el paso 3.

---

## 9. Convenciones

- **Tests con cada módulo.** Los de `rag/` son funciones puras: no hay excusa para no cubrirlas.
  El listón lo puso arbiter-mars con 533 tests; no bajes de ahí en proporción.
- **Sin `except: pass`.** Si una llamada al proveedor falla, se propaga con el contexto de qué
  consulta la causó.
- **Claves solo por entorno.** `.env.example` versionado, `.env` nunca.
- **Commits en imperativo**, describiendo el porqué. `ajusta chunking a 400 tokens: recall@5 sube
  0.81 → 0.89` es útil; `fix chunking` no.
- **Este archivo se actualiza cuando cambia una decisión de diseño**, en el mismo commit. Un
  CLAUDE.md desactualizado es peor que no tenerlo.
- Mantené un `AGENTS.md` como copia agnóstica de herramienta, igual que en arbiter-mars.

---

## 10. Definition of done

El proyecto está terminado cuando **todo** esto es cierto:

- [ ] El arnés corre con un comando y reporta las cuatro métricas.
- [ ] `groundedness` es 1.00 sobre el golden set completo.
- [ ] El sistema se abstiene correctamente en las 8 preguntas sin respuesta.
- [ ] El mismo golden set corrió contra los tres proveedores y la tabla está en el README.
- [ ] Está desplegado y hay una URL que alguien puede abrir.
- [ ] El README explica la tesis en los primeros dos párrafos, con números reales.

Cuando los seis estén tildados —**y no antes**— este bloque se agrega al CV, reemplazando los
corchetes por los números que salieron:

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

Hasta que exista, no va en el CV.
