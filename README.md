# ITSM Asistanı

ITSM / ticket chatbot prototipi. Kullanıcı doğal dille yazar; asistan **sınıflandırır**, geçmiş **çözüm kayıtlarından** önerir, eksik alanları tamamlar, ticket açar. Rapor komutları kuyruğa alınır, günlük JOB ile birim özeti üretilir.

Canlı ServiceNow yoktur. Kayıtlar JSONL.

Ayrıntı: `PRD.md`, `ARCHITECTURE.md`, `TODO.md`, `TERMS.md`.

## Ne yapar
1. Talebi anlama (gerekirse netleştirme)
2. Çözüm kaydı önerme (`data/solutions.jsonl`)
3. Ticket alanlarını tamamlama (varlık, konum, etki)
4. Sınıf: Talep → Birim → Modül → Süreç (önce anahtar kelime, belirsizse küçük TF-IDF model; eğitim `data/itsm_siniflandirma.csv` + şablonlar)
5. Rapor komutu + `python src/daily_jobs.py`

## Kurulum
```powershell
python -m venv .asude
.\.asude\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Asistanı çalıştır
```powershell
streamlit run src\app.py
```

Yönetici: `admin@reportly.local` / `AdminReportly1!`

### Demo
```
Bilgisayarım bozuldu, talep açmak istiyorum.
```
Sınıf + çözüm + eksik alan soruları, sonra ticket.

```
Laptopum açılmıyor, ekran siyah.
```
Önce çözüm kaydı; “işe yaradı” dersen kayıt açılmaz.

```
Açık taleplerin raporunu hazırla, günlük özet istiyorum.
```
Sonra: `python src\daily_jobs.py`

```powershell
python src\train_itsm_nlu.py
python src\eval_dialogues.py
```

İsteğe bağlı LLM (`ASSISTANT_USE_LLM=1`). Kararı orchestrator verir.
