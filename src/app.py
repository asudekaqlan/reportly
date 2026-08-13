"""
NLU Insight Lab — modern Streamlit UI
Run from the project root:
    streamlit run src/app.py
"""

from pathlib import Path

import joblib
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

st.set_page_config(
    page_title="NLU Insight Lab",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&family=Instrument+Serif:ital@0;1&display=swap');

:root {
  --bg: #1a2624;
  --ink: #DBD3D1;
  --muted: #A1B4A5;
  --sage: #A1B4A5;
  --line: #4a635e;
  --panel: #385752;
  --accent: #A56266;
  --accent-soft: #F5B8B6;
}

html, body, [class*="css"] {
  font-family: "DM Sans", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(900px 420px at 12% -10%, rgba(165, 98, 102, 0.28) 0%, transparent 55%),
    radial-gradient(800px 380px at 100% 0%, rgba(161, 180, 165, 0.18) 0%, transparent 50%),
    linear-gradient(180deg, #14201e 0%, var(--bg) 45%, #121c1a 100%);
  color: var(--ink);
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
#MainMenu, footer { visibility: hidden; }

.block-container {
  padding-top: 2.5rem;
  padding-bottom: 3rem;
  max-width: 680px;
  text-align: center;
}

/* Also center Streamlit markdown wrappers */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] div {
  text-align: center !important;
}

.hero {
  animation: rise 0.7s ease-out both;
  margin: 0 auto 1.75rem;
  text-align: center !important;
  width: 100%;
}

.brand {
  font-family: "Instrument Serif", Georgia, serif;
  font-size: clamp(2.6rem, 6vw, 3.6rem);
  line-height: 1.05;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0 auto 0.65rem auto;
  text-align: center !important;
  width: 100%;
}

.brand em {
  font-style: italic;
  color: var(--accent-soft);
}

.lede {
  font-size: 1.05rem;
  line-height: 1.55;
  color: var(--muted);
  max-width: 28rem;
  margin: 0 auto !important;
  text-align: center !important;
  animation: rise 0.85s ease-out both;
  display: block;
  width: 100%;
}

.section-label {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--sage);
  margin: 0 auto 0.75rem auto !important;
  text-align: center !important;
  display: block;
  width: 100%;
}

.result-box {
  margin: 1.25rem auto 0;
  text-align: center;
  background: rgba(56, 87, 82, 0.85);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.35rem 1.4rem 1.2rem;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
  animation: rise 0.55s ease-out both;
}

.result-kicker {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-soft);
  margin-bottom: 0.4rem;
}

.result-title {
  font-family: "Instrument Serif", Georgia, serif;
  font-size: 1.75rem;
  line-height: 1.25;
  margin: 0 0 0.85rem 0;
  color: var(--ink);
}

.meter {
  height: 8px;
  background: #2c3f3b;
  border-radius: 999px;
  overflow: hidden;
  margin: 0.5rem auto 0.4rem;
  max-width: 280px;
}

.meter > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #A1B4A5, #A56266);
  border-radius: 999px;
  transform-origin: left center;
  animation: fill 0.8s ease-out both;
}

.meter-caption {
  font-size: 0.92rem;
  color: var(--muted);
  margin-bottom: 0.9rem;
}

.alt-list {
  text-align: left !important;
  max-width: 360px;
  margin: 0 auto;
}

.alt-list,
.alt-list .alt-row,
.alt-list .alt-name,
.alt-list .alt-score {
  text-align: left !important;
}

.alt-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--line);
  font-size: 0.95rem;
  text-align: left !important;
}

.alt-row:last-child { border-bottom: none; }
.alt-name { color: var(--ink); }
.alt-score { color: var(--muted); font-variant-numeric: tabular-nums; }

.alt-heading {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--sage);
  margin: 0.4rem 0 0.2rem;
  text-align: center;
}

.hint {
  margin-top: 1.4rem;
  font-size: 0.88rem;
  color: var(--muted);
  text-align: center;
}

/* Hide label spacers / empty boxes */
[data-testid="stWidgetLabel"] { display: none !important; }

.stTextArea,
.stTextArea > div,
.stTextArea textarea {
  width: 100% !important;
}

.stTextArea textarea {
  border-radius: 12px !important;
  border: 1px solid var(--line) !important;
  background: #243330 !important;
  height: 160px !important;
  min-height: 160px !important;
  max-height: 160px !important;
  resize: none !important;
  font-size: 1rem !important;
  line-height: 1.5 !important;
  color: #DBD3D1 !important;
  caret-color: #F5B8B6 !important;
  text-align: left !important;
}

.stTextArea textarea::placeholder {
  color: #8fa397 !important;
}

.stTextArea textarea:focus {
  border-color: #A1B4A5 !important;
  box-shadow: 0 0 0 3px rgba(245, 184, 182, 0.28) !important;
}

/* Hide Streamlit resize handle */
.stTextArea [data-testid="stMarkdownContainer"],
div[data-baseweb="textarea"] {
  resize: none !important;
}
.stTextArea svg,
.stTextArea [class*="resize"],
.stTextArea + div {
  /* no-op; resize disabled below */
}
textarea {
  resize: none !important;
}

div.stButton {
  display: flex;
  justify-content: center;
}

div.stButton > button {
  width: 100%;
  max-width: 680px;
  background: #A56266 !important;
  color: #DBD3D1 !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.7rem 1rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: transform 0.15s ease, background 0.15s ease !important;
}

div.stButton > button:hover {
  background: #F5B8B6 !important;
  color: #1a2624 !important;
  transform: translateY(-1px);
}

[data-testid="stAlert"] {
  background: #385752 !important;
  color: #DBD3D1 !important;
  border: 1px solid #A1B4A5 !important;
  text-align: center;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fill {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
</style>
"""


@st.cache_resource
def load_artifacts():
    vectorizer_path = MODELS_DIR / "tfidf_vectorizer.joblib"
    model_path = MODELS_DIR / "logreg_model.joblib"
    if not vectorizer_path.exists() or not model_path.exists():
        return None, None
    vectorizer = joblib.load(vectorizer_path)
    model = joblib.load(model_path)
    return vectorizer, model


def predict_text(vectorizer, model, text: str, top_k: int = 3):
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    classes = model.classes_
    ranked = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)
    return pred, float(max(proba)), ranked[:top_k]


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "prediction" not in st.session_state:
        st.session_state.prediction = None

    st.markdown(
        """
        <div class="hero">
          <h1 class="brand">NLU <em>Insight</em> Lab</h1>
          <p class="lede">
            Enter a complaint; the model will predict the product category and confidence score.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    vectorizer, model = load_artifacts()
    if vectorizer is None or model is None:
        st.error(
            "Model files not found. From the project root, run "
            "`python src\\classic_nlu.py` first."
        )
        st.stop()

    st.markdown('<p class="section-label">Complaint text</p>', unsafe_allow_html=True)

    text = st.text_area(
        "complaint_input",
        height=160,
        placeholder="My student loan servicer never applied my payments correctly.",
        label_visibility="collapsed",
        key="complaint_text",
    )

    run = st.button("Predict category", type="primary", use_container_width=True)

    if run:
        cleaned = text.strip()
        if not cleaned:
            st.session_state.prediction = None
            st.warning("Please enter some text.")
        else:
            pred, confidence, top = predict_text(vectorizer, model, cleaned)
            st.session_state.prediction = {
                "pred": pred,
                "confidence": confidence,
                "top": top,
            }

    if st.session_state.prediction:
        pred = st.session_state.prediction["pred"]
        confidence = st.session_state.prediction["confidence"]
        top = st.session_state.prediction["top"]
        pct = int(round(confidence * 100))

        alts_html = "".join(
            f'<div class="alt-row"><span class="alt-name">{label}</span>'
            f'<span class="alt-score">{score:.1%}</span></div>'
            for label, score in top
        )

        st.markdown(
            f"""
            <div class="result-box">
              <div class="result-kicker">Prediction result</div>
              <h2 class="result-title">{pred}</h2>
              <div class="meter"><span style="width:{pct}%"></span></div>
              <div class="meter-caption">Confidence: {confidence:.3f} ({pct}%)</div>
              <div class="alt-heading">Top 3 probabilities</div>
              <div class="alt-list">{alts_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p class="hint">Engine: TF-IDF + Logistic Regression · Data: CFPB Consumer Complaints sample</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
