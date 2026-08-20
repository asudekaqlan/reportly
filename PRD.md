# Product Requirements — ITSM Asistanı

Repo: `nlu-insight-lab`. Product: **ITSM Asistanı**, an AI-supported first-line chatbot on a demo ITSM/ticket process.

## 1. Overview
The user describes a request in natural language. The bot classifies it as **Talep → Birim → Modül → Süreç/Talep tipi**, offers matching past **solution records**, collects missing ticket fields, then opens a structured ticket. Reporting commands are queued for a daily JOB.

There is **no** live ServiceNow/Jira. Tickets are JSONL. Solutions are a seeded knowledge file.

## 2. Personas
- **Employee / requester:** Opens incidents and service requests in chat.
- **ITSM admin:** Reads the classified queue and report JOB output.

## 3. Current prototype

1. **Talebi anlama** — keyword taxonomy first; if unclear, a small TF-IDF + logistic regression classifier; clarify when still unsure.
2. **Çözüm önerme** — retrieve from `data/solutions.jsonl` (past ITSM solution records).
3. **Veri tamamlama** — required fields: varlık, konum, etki.
4. **Sınıflandırma** — 4-level path, shown in the bubble meta and on the ticket.
5. **Raporlama** — “rapor / günlük özet / açık talepler” queues a job; `python src/daily_jobs.py` writes the unit summary.

## 4. Out of scope
Live CMDB, real mail gateways, ServiceNow APIs, marketplace returns.

## 5. Success
Demo sentences: laptop arızası → çözüm; “talep aç” → alanlar → ticket; belirsiz metin → netleştirme; rapor komutu → kuyruk.
