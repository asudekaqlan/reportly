# Architecture — Reportly

Python + Streamlit. No API gateway and no SQL database in the current build.

## 1. Runtime flow

```text
Customer message (English)
    → nlu_engine.predict_category
    → sentiment.analyze_sentiment
    → intents.detect_intents
    → rules.match_rule
    → orchestrator.handle_turn
         ├─ rule reply          (phase: waiting_if_resolved)
         ├─ create ticket       (phase: ticket_open)
         └─ ticket follow-up    (phase: ticket_open)
    → app.py renders customer chat, or the admin queue after admin login
```

Phases in session state: `open` → `waiting_if_resolved` → `ticket_open`.

Decision order (see `orchestrator.py`): resolved thanks; follow-up on an open ticket; waiting follow-up; file complaint / still unresolved; force ticket (high-risk or `usually_resolves=False`); rule reply; else ticket (no rule).

## 2. Modules

| File | Role |
|---|---|
| `src/nlu_engine.py` | Load `models/tfidf_vectorizer.joblib` + `logreg_model.joblib` |
| `src/classic_nlu.py` | Train those artifacts from `data/processed/complaints_clean.csv` |
| `src/sentiment.py` | Lexicon: angry / negative / calm, high_risk |
| `src/intents.py` | file_complaint, still_unresolved |
| `src/rules.py` | Eight procedures; score = keyword hits + category substring bonus |
| `src/summaries.py` | Template manager bullets + record notes; optional LLM copy via `llm_analyze.py` |
| `src/llm_analyze.py` | Ollama rewrite of bullets/notes only (`ASSISTANT_USE_LLM=1`); never decides |
| `src/tickets.py` | Append/update `data/tickets.jsonl`; follow-ups stay on the same id |
| `src/orchestrator.py` | Single turn policy |
| `src/auth.py` | Local JSONL accounts (`data/users.jsonl`); customer vs admin |
| `src/app.py` | UI only |

Keep new behavior in the matching layer. Do not put rule or ticket logic inside Streamlit callbacks beyond calling `handle_turn`.

## 3. Ticket record (current)

Not a UUID CRM object. Id format: `T-YYYYMMDD-0001`.

```text
id, created_at
urgency: high | medium
category: CFPB product string (or Unknown)
category_confidence: float
sentiment: angry | negative | calm
customer_ask, tried_rules[], why_unresolved
summary_bullets[], recommended_next_step, handoff_notes (record notes)
followups[] (extra detail after the record is open)
status: open | in_progress | resolved
```

There is no `customerId`, `clusterId`, or `frustrationLevel` enum. Urgency is derived: high if angry or high_risk, else medium.

## 4. Data

- Raw CFPB: `data/raw/complaints.csv` (not in git)
- Sample / clean: `data/processed/complaints_sample.csv`, `complaints_clean.csv`
- Tickets: `data/tickets.jsonl` (gitignored)
- Accounts: `data/users.jsonl` (gitignored)
- Labels stay English product names from CFPB

## 5. Later architecture (do not build until asked)

- Optional `cluster_id` + similarity over ticket summaries for an admin ranking view
