# Reportly

Rule-first complaint assistant. It tries a standard procedure, then opens a specialist record with a manager brief if that fails or the customer asks. Angry customers can request a formal complaint.

The old NLU lab (TF-IDF + logistic regression on CFPB complaints) is still the category engine behind the assistant.

See `PRD.md`, `ARCHITECTURE.md`, `TODO.md`, and `TERMS.md`.

## What it does
- Classifies the product/category of a complaint
- Detects tone (angry / negative / calm) and intents (file a complaint, still unresolved)
- Matches 8 self-serve rules before opening a record
- Opens a structured ticket when rules cannot finish the job
- Keeps extra detail on the same record (no second ticket)
- Customer home is the chat; supervisors read the queue after admin login

## Setup
```powershell
python -m venv .asude
.\.asude\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Data and category model
The raw file (`data/raw/complaints.csv`) is not in the repo.
Download CFPB / Kaggle Consumer Complaints and save it as `data/raw/complaints.csv`.

Then train the category model (optional but recommended):
```powershell
python src\prepare_sample.py
python src\explore_clean.py
python src\classic_nlu.py
```

The assistant still runs without `models/`; rules and tickets work, category routing is weaker.

## Run the assistant
```powershell
streamlit run src\app.py
```

- **Customer home** — complaint chat and past conversations
- **Log in / Sign up** — local JSONL accounts (`data/users.jsonl`)
- **Admin login** — on the login dialog; opens the complaint queue (manager brief, notes, status)

Local demo admin: `admin@reportly.local` / `AdminReportly1!`

### Demo sentences
```
My student loan servicer never applied my payments correctly and now they say I am late even though I paid on time.
That did not help, still the same.
The last payment was on March 3, confirmation 8821.
```

Fee example that should hit a rule:
```
The bank deducted an unexpected fee from my checking account.
```

Tickets are appended to `data/tickets.jsonl`. Extra messages after a ticket is open are written onto that same record.

Optional LLM copy for the manager brief only (Ollama). The orchestrator still decides rule vs ticket:

```powershell
$env:ASSISTANT_USE_LLM = "1"
streamlit run src\app.py
```

If Ollama is down, templates are used.

Check expected actions:
```powershell
python src\eval_dialogues.py
```

## How a turn is decided
1. Category (saved model) + sentiment (lexicon) + intent (keywords)
2. Rule match (category + keywords)
3. Then one of:
   - procedure reply
   - background ticket with a supervisor brief
   - follow-up on an already open record

## Sample model result
On a 5,000-row sample (after dropping rare classes), test accuracy is about 0.64.
That number is the category engine, not the assistant. Assistant quality is whether the right rule or ticket happened.
