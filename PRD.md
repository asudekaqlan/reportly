# Product Requirements — Reportly

Repo: `reportly`. Product: **Reportly**. This PRD describes **what exists now** and **what to build next**. It is not a separate HearBack/e-commerce product.

## 1. Overview
A first-line complaint assistant. It tries a defined procedure, then opens a specialist record with a structured manager brief if that fails or the customer asks. An angry customer can request a formal complaint.

Training data is CFPB-style consumer complaints. The Streamlit UI is English.

## 2. Personas
- **Customer:** Describes a complaint in chat; wants a procedure or a complaint record. May register a local account.
- **Admin / supervisor:** Logs in separately, reads the queue: urgency, category, bullets, why unresolved, record notes. Does not yet get clustering or CRM.

## 3. Current MVP (shipped)

### A. Chat + rule-first resolution
- Natural-language complaint on the customer home.
- Category from the saved TF-IDF + logistic regression model (`models/`).
- Eight self-serve rules (payment not posted, credit report error, debt not mine, harassing calls, unauthorized charge, overdraft/fee, transfer delay, vehicle dealer vs lender).
- If a rule matches and is expected to help: procedure reply, then ask if it is resolved.

### B. Sentiment and intents
- Lexicon sentiment: `angry` / `negative` / `calm`, plus `high_risk` phrases.
- Intents: file a complaint, still unresolved, thanks/resolved.
- Angry + matching rule → offer to file a complaint; do **not** auto-ticket on anger alone.
- High-risk (fraud, identity theft, lawsuit, foreclosure, unauthorized) → ticket immediately, with the procedure text if a rule also matched.

### C. Tickets
- Ticket when: no rule, forced (high-risk / hard rule), customer files a complaint, or self-serve did not work.
- Record fields: id, urgency, category, confidence, sentiment, customer ask, rules tried, why unresolved, summary bullets, next step, record notes (`handoff_notes` in JSON), status (`open` | `in_progress` | `resolved`).
- Stored in `data/tickets.jsonl`.
- Extra detail after a ticket is open stays on the same record (`ticket_followup` writes `followups` + notes); live agent handoff is out of scope.

### D. UI
- Customer home: chat panel. The side menu lists conversations.
- Login / register (local JSONL in `data/users.jsonl`).
- Admin login opens the complaint queue (ticket inspector + status actions).
- Debug line under assistant replies: topic, sentiment, rule, action.

## 4. Out of scope for now
Semantic clustering, UUID CRM, TypeScript/API backend, RFM, forecasting. Do not implement these unless this PRD’s “later” section is explicitly chosen.

## 5. Later (when the MVP is stable)
Similar-ticket grouping for the admin view.

## 6. Success
Category accuracy (~0.64 on the sample) is the NLU engine, not the product. Assistant success: the right **rule or ticket** on the demo scenarios, and a manager who can read a ticket in about ten seconds.
