# Architecture — ITSM Asistanı

Python + Streamlit. No API gateway and no SQL database in the current build.

## 1. Runtime flow

```text
User message
    → taxonomy.classify_request          (keywords first, TF-IDF fallback)
    → sentiment / intents / report cmd
    → solutions.find_solutions           (past ITSM KB)
    → slots (asset, location, impact)
    → orchestrator.handle_turn
         ├─ clarify
         ├─ suggest_solution
         ├─ collect_fields
         ├─ ticket_open
         └─ report_queued
    → app.py: requester chat, or admin queue
```

Daily JOB: `python src/daily_jobs.py` runs queued report commands and stores the unit summary.

## 2. Modules

| File | Role |
|---|---|
| `src/taxonomy.py` | 4-level ITSM classification (keyword, then small classifier) |
| `src/itsm_nlu.py` | TF-IDF + logreg süreç fallback (`models/itsm_*.joblib`) |
| `src/train_itsm_nlu.py` | Retrain the ITSM classifier |
| `src/solutions.py` | Retrieve solution records |
| `src/slots.py` | Required ticket fields |
| `src/reports.py` / `src/daily_jobs.py` | Report commands + JOB |
| `src/sentiment.py` / `src/intents.py` / `src/rules.py` | Tone, ticket intent, high-severity skip-KB |
| `src/summaries.py` | Admin brief |
| `src/llm_analyze.py` | Optional Ollama copy; never decides |
| `src/tickets.py` | `data/tickets.jsonl` |
| `src/orchestrator.py` | Turn decision |
| `src/auth.py` | Local accounts |
| `src/app.py` | UI only |

Marketplace TF-IDF files (`classic_nlu.py`, `nlu_engine.py`, `models/tfidf_vectorizer.joblib`) remain in the repo but are not on the ITSM decision path. Retrain ITSM NLU with `python src/train_itsm_nlu.py`.

## 3. Record

Id: `T-YYYYMMDD-0001`.

```text
talep_turu / birim / modul / surec (+ labels)
asset, location, impact
status: open | in_progress | resolved
```

## 4. Data

- `data/solutions.jsonl` — seeded past solutions
- `data/itsm_siniflandirma.csv` — 1000 labeled Turkish requests; trainer maps overlapping süreç labels onto the 9 prototype classes
- `data/tickets.jsonl` — runtime tickets
- `data/report_jobs.jsonl` — queued / sent reports
