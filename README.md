# NLU Insight Lab

A Python project that predicts product/category labels from customer complaint texts.

## What it does
- Samples the CFPB Consumer Complaints dataset
- Cleans the texts
- Classifies with TF-IDF + Logistic Regression
- Predicts new texts with a saved model
- Provides a modern Streamlit demo UI

## Setup
```powershell
python -m venv .asude
.\.asude\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Data
The raw file (`data/raw/complaints.csv`) is not in the repo.
Download CFPB / Kaggle Consumer Complaints and save it as `data/raw/complaints.csv`.

Then run:
```powershell
python src\prepare_sample.py
python src\explore_clean.py
python src\classic_nlu.py
```

## Prediction (terminal)
```powershell
python src\predict.py
```

## UI
After training (`models/` must exist):
```powershell
streamlit run src\app.py
```

Open the browser page, paste a complaint, and get a prediction.

## Sample result
On a 5,000-row sample (after dropping rare classes), test accuracy is about 0.64.
