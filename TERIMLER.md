# Reportly — Bilmen gereken terimler

Sıfırdan bakıyorsan bu dosya yeter. Her maddede: **ne**, **bu projede ne işe yarar**, **ne kadar derinlemesine bilmen lazım**.

Kutu şimdilik **İngilizce** şikayet ister. Arayüz Türkçe olabilir.

---

## A. Ürün ve gösteri

### Reportly
Şikayet asistanının adı. Önce kural dener; yetmezse yönetici özetiyle kayıt açar.

### CFPB
ABD tüketici finans şikayetleri (kamu verisi). Kaggle’dan indirdiğin `complaints.csv` bu. Metinler İngilizce; kategoriler `Student loan`, `Mortgage` vb.

### Demo
Mülakatta / kendine gösterirken oynayacağın **sabit senaryo**. Rastgele yazmak değil. Replikler: `README.md` içindeki Demo sentences. Amaç 2 dakikada üç kapıyı göstermek: kural → ticket → aynı kayda ek detay.

### Demo ezberlemek
Model matematiğini ezberlemek değil. Ne **söyleyeceğini** ve kutuya **hangi İngilizce cümleyi yapıştıracağını** birkaç kez prova etmek.

---

## B. Metin → sayı → kategori (NLU motoru)

### NLU (Natural Language Understanding)
Bilgisayarın metinden “ne hakkında / ne istiyor?” çıkarması. Burada dar hali: **ürün kategorisi** tahmini.

### Kategori (category)
Şikayetin ürünü: öğrenci kredisi, ipotek, tahsilat… Modelin çıktısı. Asistan cevabı değil; **yönlendirme sinyali**. Kutu altında `konu: Student loan (72%)`.

### Bag of words
Cümleyi kelime çantası saymak; sıra unutulur. TF-IDF’in kaba atası.

### TF (Term Frequency)
Bir kelime **bu şikayette** ne kadar sık? Uzun metin ezmesin diye genelde oran.

### IDF (Inverse Document Frequency)
Kelime **tüm veri setinde** ne kadar nadir? Her yerde geçen (`the`, `account`) sönük; az belgede geçen (`foreclosure`) parlak.

### TF-IDF
TF × IDF. Metni sayı listesine çevirir: “burada sık + koleksiyonda nadir = önemli.” Reportly’de `TfidfVectorizer`, en fazla 5000 özellik, 1–2 kelimelik kalıplar (ngram). **Anlamaz**; kelime örtüşmesine bakar. Türkçe yazınca İngilizce sütunlar 0 kalır.

### n-gram
1-gram: tek kelime (`loan`). 2-gram: iki kelime (`student loan`). Kodda `ngram_range=(1, 2)`.

### Vektör / özellik (feature)
Her şikayetin TF-IDF sayı listesi. Model ancak bununla çalışır.

### Lojistik regresyon
Bu sayılara **ağırlık** verip 0–1 **olasılık** üretir; en yüksek olasılıklı kategoriyi seçer. “Regresyon” adı yanıltır: burada **sınıflandırıcıdır**. Chat değildir. `LogisticRegression` + `predict` / `predict_proba`.

### Sınıflandırma (classification)
Girdi → sonlu etiketlerden biri. Fiyat tahmini (regresyon) değil.

### Olasılık / güven (confidence)
Kazanan sınıfın `predict_proba` değeri. `%64` doğrulukla karıştırma: güven **bu mesaj için** “ne kadar emin?”

### Accuracy (~%64)
Testte 100 şikayetten kaçı doğru kategori. **Asistan başarısı bu değil.** Asistan: doğru kural veya ticket oldu mu?

### Train / test split
Verinin bir kısmıyla öğren (`fit`), görmediği kısmıyla sına. Ezberi yakalamak için. Sizde kabaca %80 / %20, `stratify` = kategori oranları korunsun.

### Overfit (ezber)
Eğitim setini ezberleyip yeni metinde batmak. Test seti bunun için var.

### Etiket (label)
İnsanın (CFPB’nin) koyduğu doğru kategori. Model bunu taklit etmeye çalışır.

---

## C. Asistan beyni (kural, ticket)

### Orchestrator
`orchestrator.py`. Her mesajda **hangi kapı?** diye karar veren kod. LLM değil; sıralı `if`. Beyin burada.

### Kural (rule)
“Şu kelimeler + şu kategori → şu hazır metin.” 8 tane. Hesabı düzeltmez; **prosedür** söyler (referans no, 3–5 gün…). `rules.py`.

### Prosedür
Kural tutunca basılan adım listesi. “Ticket açmadan dene.”

### Intent (niyet)
Kategori değil: müşteri **ne istiyor?** Şikayet aç, hâlâ bozuk, teşekkür. `intents.py`, İngilizce kalıplar (`file a complaint`, `did not help`).

### Sentiment (duygu)
Sözlük: `angry` / `negative` / `calm`. Şikayetler zaten olumsuz; asıl ayrım **patlamak üzere mi?** Kızgınlık tek başına sessiz ticket açmaz; teklif eder. `sentiment.py`.

### High-risk
Fraud, identity theft, lawsuit, foreclosure, unauthorized. Bunlarda kural yetmez → **hemen ticket**.

### Ticket
Uzman / yönetici kaydı. `T-YYYYMMDD-0001`. Alanlar: aciliyet, kategori, özet maddeleri, neden bitmedi, kayıt notu. `data/tickets.jsonl`.

### Urgency (aciliyet)
`high` (kızgın veya high-risk) veya `medium`. Öncelik sırası.

### Manager brief (yönetici özeti)
Ticket’taki 3 kısa madde. 10 saniyede okunsun. `summaries.py`.

### Kayıt notu
Ticket’taki konuşma özeti (`handoff_notes` alanı). Canlı hat yok; yönetici hikâyeyi kayıttan okusun.

### Phase (durum)
Sohbetin hangi kapıda olduğu: `open` → `waiting_if_resolved` → `ticket_open`. Orchestrator buna göre davranır.

### Containment
Kaç kişi kayıt açılmadan bitti. İleride asistan metriği; şimdilik demo yolları.

### Eskalasyon
Bottan kayda çıkmak. Ticket bunun somut hali.

---

## D. Araçlar ve dosyalar

### Streamlit
Python ile tarayıcı arayüzü. `streamlit run src/app.py` → `http://localhost:8501`. Müşteri sohbeti ana sayfa; yönetici kuyruğu ayrı girişle. React/`npm run dev` değil.

### Sanal ortam (venv, `.asude`)
Bu projeye özel Python + paketler. Satırda `(.asude)` görünsün. `Activate.ps1` ile girilir; `deactivate` ile çıkılır. Silme.

### joblib
Eğitilmiş modeli diske yazıp okuma. `models/tfidf_vectorizer.joblib`, `logreg_model.joblib`.

### JSONL
Her satır bir JSON. Ticket’lar böyle birikir.

### LLM (büyük dil modeli)
ChatGPT / Ollama benzeri. Kararı **vermez**. İsteğe bağlı özet metni için (`ASSISTANT_USE_LLM=1`); kapalıysa şablon özet kullanılır.

### Ollama
Bilgisayarda yerel model çalıştırma. Zorunlu değil.

---

## E. Kısa zincir (ezberlenecek tek şema)

```text
İngilizce şikayet
  → TF-IDF (sayı)
  → lojistik regresyon (kategori + %)
  → duygu + niyet
  → kural eşleşir mi?
       evet ve sakin       → prosedür
       olmadı / yok / risk → ticket
       kayıt açıkken detay → aynı ticket (followup)
```

Daha derin matematik gerekmez; mülakatta bu şema + `README.md` Demo sentences yeter.
