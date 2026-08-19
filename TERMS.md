# Reportly — terms you need

If you are starting from zero, this file is enough. Each item: **what it is**, **what it does here**, **how deep you need to go**.

---

## A. Product and demo

### Reportly
The complaint assistant. It tries a rule first; if that is not enough it opens a record with a manager brief.

### CFPB
US consumer finance complaints (public data). The `complaints.csv` you download from Kaggle. Texts and labels are English product names such as `Student loan` and `Mortgage`.

### Demo
A **fixed scenario** you play in an interview or for yourself. Not random typing. Lines: Demo sentences in `README.md`. Goal: show three doors in two minutes — rule → ticket → extra detail on the same record.

### Memorizing the demo
Not the model math. Rehearse **what you will say** and **which sentence you paste** into the box.

---

## B. Text → numbers → category (NLU engine)

### NLU (Natural Language Understanding)
The computer extracting “what is this about / what do they want?” from text. Here, the narrow form: **product category** prediction.

### Category
The product of the complaint: student loan, mortgage, collections… The model’s output. Not the assistant reply; a **routing signal**. Under the box: `topic: Student loan (72%)`.

### Bag of words
Treat the sentence as a bag of words; order is forgotten. The crude ancestor of TF-IDF.

### TF (Term Frequency)
How often a word appears **in this complaint**. Usually a ratio so long text does not dominate.

### IDF (Inverse Document Frequency)
How rare a word is **across the dataset**. Words everywhere (`the`, `account`) fade; words in few documents (`foreclosure`) stand out.

### TF-IDF
TF × IDF. Turns text into a list of numbers: “frequent here + rare in the collection = important.” Reportly uses `TfidfVectorizer`, at most 5000 features, 1–2 word patterns (ngrams). It does **not** understand meaning; it looks at word overlap.

### n-gram
1-gram: one word (`loan`). 2-gram: two words (`student loan`). In code: `ngram_range=(1, 2)`.

### Vector / feature
Each complaint’s TF-IDF number list. The model can only work with this.

### Logistic regression
Gives those numbers **weights** and produces a 0–1 **probability**; picks the highest-probability category. The name “regression” is misleading: here it is a **classifier**. It is not chat. `LogisticRegression` + `predict` / `predict_proba`.

### Classification
Input → one of a finite set of labels. Not price prediction (regression).

### Probability / confidence
The `predict_proba` value of the winning class. Do not confuse with ~64% accuracy: confidence is “how sure **for this message**?”

### Accuracy (~64%)
How many of 100 test complaints got the right category. **That is not assistant success.** Assistant success: did the right rule or ticket happen?

### Train / test split
Learn on part of the data (`fit`), test on the unseen part. To catch memorization. Here roughly 80% / 20%, `stratify` = keep category ratios.

### Overfit
Memorizing the training set and failing on new text. The test set exists for this.

### Label
The correct category a human (CFPB) assigned. The model tries to copy that.

---

## C. Assistant brain (rule, ticket)

### Orchestrator
`orchestrator.py`. The code that decides **which door?** on each message. Not an LLM; sequential `if`. The brain lives here.

### Rule
“These words + this category → this canned text.” There are 8. It does not fix the account; it speaks a **procedure** (reference number, 3–5 days…). `rules.py`.

### Procedure
The step list printed when a rule matches. “Try this before opening a ticket.”

### Intent
Not category: what does the customer **want**? File a complaint, still broken, thanks. `intents.py`, phrases such as `file a complaint`, `did not help`.

### Sentiment
Lexicon: `angry` / `negative` / `calm`. Complaints are already negative; the real split is **about to explode?** Anger alone does not silently open a ticket; it offers one. `sentiment.py`.

### High-risk
Fraud, identity theft, lawsuit, foreclosure, unauthorized. A rule is not enough → **ticket immediately**.

### Ticket
Specialist / manager record. `T-YYYYMMDD-0001`. Fields: urgency, category, summary bullets, why it did not finish, record notes. `data/tickets.jsonl`.

### Urgency
`high` (angry or high-risk) or `medium`. Priority order.

### Manager brief
Three short bullets on the ticket. Readable in ten seconds. `summaries.py`.

### Record notes
Conversation summary on the ticket (`handoff_notes` field). No live line; the manager reads the story from the record.

### Phase
Which door the chat is in: `open` → `waiting_if_resolved` → `ticket_open`. The orchestrator behaves accordingly.

### Containment
How many people finished without a record. A later assistant metric; for now, demo paths.

### Escalation
Leaving the bot for a record. A ticket is the concrete form of that.

---

## D. Tools and files

### Streamlit
Browser UI in Python. `streamlit run src/app.py` → `http://localhost:8501`. Customer chat is the home page; the admin queue is a separate login. Not React / `npm run dev`.

### Virtual environment (venv, `.asude`)
Python + packages for this project only. You should see `(.asude)` on the prompt. Enter with `Activate.ps1`; leave with `deactivate`. Do not delete it.

### joblib
Write and read a trained model from disk. `models/tfidf_vectorizer.joblib`, `logreg_model.joblib`.

### JSONL
One JSON object per line. Tickets accumulate this way.

### LLM (large language model)
ChatGPT / Ollama style. It does **not** decide. Optional copy for summaries (`ASSISTANT_USE_LLM=1`); templates are used when it is off.

### Ollama
Run a local model on the machine. Not required.

---

## E. Short chain (the one schema to remember)

```text
complaint
  → TF-IDF (numbers)
  → logistic regression (category + %)
  → sentiment + intent
  → does a rule match?
       yes and calm           → procedure
       no / unresolved / risk → ticket
       extra detail on open   → same ticket (followup)
```

Deeper math is not needed; this schema plus `README.md` Demo sentences is enough for an interview.
