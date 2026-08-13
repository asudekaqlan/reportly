# NLU Insight Lab

Musteri sikayet metinlerinden urun/kategori tahmini yapan Python projesi.

## Ne yapiyor?
- CFPB Consumer Complaints verisinden orneklem alir
- Metinleri temizler
- TF-IDF + Logistic Regression ile siniflandirma yapar
- Kayitli model ile yeni metin tahmini yapar

## Kurulum
```powershell
python -m venv .asude
.\.asude\Scripts\Activate.ps1
python -m pip install -r requirements.txt