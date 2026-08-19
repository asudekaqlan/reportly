# TODO — Reportly

Work top to bottom. Do not start Later items before Now is done. Customer chat stays **English**.

## Done
- [x] Rule-first orchestrator (8 rules, sentiment, intents)
- [x] Tickets + manager brief (`data/tickets.jsonl`)
- [x] Streamlit: customer chat home + admin complaint queue
- [x] Local JSONL accounts (customer register / login, admin queue)
- [x] CFPB category model (TF-IDF + logreg, ~0.64)
- [x] `PRD.md` / `ARCHITECTURE.md` / `.cursorrules` aligned to this repo
- [x] 4 demo paths + 10 expected-action dialogues (`python src/eval_dialogues.py`)
- [x] Bank/checking fee rule (`Bank account or service`, `unexpected fee`)
- [x] README: English-only warning, demo sentences, doc links
- [x] Tighten 8 rules (category aliases + fee keywords)
- [x] Shorter manager brief (`summaries.py`, 3 bullets)
- [x] Ticket statuses: `in_progress` / `resolved`
- [x] Ticket follow-up writes extra detail onto the same JSONL record
- [x] Optional LLM for bullets/record notes only (`ASSISTANT_USE_LLM=1`), orchestrator still decides

## Later
- [ ] Similar-ticket grouping on the admin queue

## Won’t do (unless PRD changes)
- Translate CFPB to Turkish / Turkish NLU in the live box
- HearBack e-commerce rewrite, TypeScript API, real CRM
- RFM, forecasting, scraping Şikayetvar
