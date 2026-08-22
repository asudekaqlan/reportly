"""
ITSM Asistanı — Streamlit UI
Run from the project root:
    streamlit run src/app.py
"""

import base64
import html
import re
from pathlib import Path

import streamlit as st

from orchestrator import handle_turn
from tickets import load_tickets

ROOT = Path(__file__).resolve().parent.parent


def _brand_font_face() -> str:
    path = ROOT / "assets" / "fonts" / "Calfinedemo.otf"
    if not path.exists():
        return ""
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        "@font-face {"
        '  font-family: "Calfine";'
        f"  src: url(data:font/otf;base64,{payload}) format('opentype');"
        "  font-weight: 400;"
        "  font-style: normal;"
        "  font-display: swap;"
        "}"
    )


st.set_page_config(
    page_title="ITSM Asistanı",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

WELCOME_MESSAGE = (
    "Merhaba, ben ITSM asistanın. "
    "Talebini doğal dille yaz; sınıflandırır, varsa çözüm kaydı öneririm, "
    "gerekirse eksik alanları tamamlayıp ticket açarım.\n\n"
    "Örneğin: *Bilgisayarım bozuldu, talep açmak istiyorum.*"
)

CUSTOM_CSS = """
<style>
""" + _brand_font_face() + """
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@1,700&family=Figtree:ital,wght@0,400;0,500;0,600;0,650;1,300;1,400&display=swap');

:root {
  --olive-deep: #4D5A2E;
  --olive: #5E5C2D;
  --moss: #8A8C41;
  --sage: #999A57;
  --mustard: #C4BA65;
  --sand: #C8B891;
  --peach: #E1A794;
  --apricot: #FEC67C;
  --orange: #FC9C51;
  --blush: #F9BDB0;
  --salmon: #E9767F;
  --mauve: #A16A84;
  --cream: #F3EBE0;
  --paper: #F3EBE0;
  --ink: #F4EAD4;
  --muted: #D5C9A8;
  --panel-radius: 22px;
}

html, body, [class*="css"] {
  font-family: "Figtree", sans-serif;
  color: var(--ink);
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  min-height: 100vh;
  box-sizing: border-box;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
section.main {
  background: transparent !important;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.stMain {
  width: 100% !important;
  max-width: 100% !important;
}

.stApp {
  color: var(--ink);
  background-color: #B7A56E !important;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: -28%;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 42% 36% at 18% 28%, #C96B2A 0%, transparent 62%),
    radial-gradient(ellipse 38% 42% at 82% 18%, #C45A64 0%, transparent 60%),
    radial-gradient(ellipse 46% 40% at 72% 78%, #8A8340 0%, transparent 64%),
    radial-gradient(ellipse 40% 34% at 12% 82%, #5E5C2D 0%, transparent 58%),
    radial-gradient(ellipse 36% 38% at 48% 48%, #C48B7A 0%, transparent 55%),
    radial-gradient(ellipse 30% 28% at 58% 12%, #D4A45A 0%, transparent 52%),
    radial-gradient(ellipse 28% 32% at 38% 88%, #7D5268 0%, transparent 58%),
    radial-gradient(ellipse 50% 40% at 50% 50%, #A67C68 0%, transparent 70%);
  filter: blur(56px) saturate(1.12);
  animation: plasma-drift 22s ease-in-out infinite;
}

.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 30% 20%, rgba(255,255,255,.12), transparent 42%),
    radial-gradient(circle at 80% 70%, rgba(77, 90, 46, .18), transparent 46%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.45'/%3E%3C/svg%3E");
  opacity: 0.38;
  mix-blend-mode: overlay;
  animation: mist-shift 18s ease-in-out infinite;
}

@keyframes plasma-drift {
  0%   { transform: translate(0, 0) rotate(0deg) scale(1); }
  35%  { transform: translate(5%, -4%) rotate(9deg) scale(1.08); }
  60%  { transform: translate(-4%, 5%) rotate(-7deg) scale(1.04); }
  100% { transform: translate(0, 0) rotate(0deg) scale(1); }
}

@keyframes mist-shift {
  0%, 100% { opacity: 0.38; }
  50% { opacity: 0.55; }
}

header[data-testid="stHeader"],
header.stAppHeader,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
.stDeployButton,
div[data-testid="stMain"] > div[data-testid="stHeader"] {
  display: none !important;
  height: 0 !important;
}

#MainMenu, footer { visibility: hidden; }

/* Streamlit container temizlikleri */
[data-testid="stElementContainer"]:has(style),
.stElementContainer:has(style) {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}

section.main, [data-testid="stMain"], [data-testid="stAppViewContainer"] {
  padding-top: 0 !important;
}

.block-container,
[data-testid="stMainBlockContainer"],
.stMainBlockContainer {
  position: relative;
  z-index: 1;
  padding: 1.8rem clamp(1.4rem, 4vw, 3.2rem) 1.8rem !important;
  max-width: 1360px !important;
  margin: 0 auto !important;
  box-sizing: border-box !important;
}

/* Başlık Alanı */
.page-head {
  margin: 0 0 1.35rem 0 !important;
  text-align: left;
}

.page-title {
  font-family: "Bodoni Moda", serif !important;
  font-style: italic !important;
  font-weight: 700 !important;
  font-size: clamp(2.4rem, 5vw, 3.6rem) !important;
  line-height: 1.08;
  letter-spacing: 0.01em;
  text-transform: none;
  color: var(--paper);
  margin: 0 !important;
  text-shadow: 0 4px 18px rgba(77, 90, 46, 0.35);
}

.page-sub {
  margin: 0.45rem 0 0 0 !important;
  color: var(--paper);
  opacity: 0.88;
  font-family: "Figtree", sans-serif;
  font-style: italic;
  font-size: 1.02rem;
  font-weight: 300;
  line-height: 1.5;
  letter-spacing: 0.01em;
  max-width: 52rem;
}

/* Kolon ve Panel Düzeni */
[data-testid="stHorizontalBlock"] {
  gap: 1.4rem !important;
  align-items: stretch !important;
}

/* Sol Panel Header Wrapper (Yeni Sohbet Butonu İçeren Satır) */
[data-testid="stHorizontalBlock"]:has(.st-key-btn_new_chat) {
  background: rgba(31, 36, 18, 0.25) !important;
  border: 1px solid rgba(246, 239, 224, 0.28) !important;
  border-bottom: 1px solid rgba(246, 239, 224, 0.16) !important;
  border-radius: var(--panel-radius) var(--panel-radius) 0 0 !important;
  padding: 0.5rem 1.15rem !important;
  margin: 0 !important;
  align-items: center !important;
  min-height: 3.5rem !important;
  box-sizing: border-box !important;
  backdrop-filter: blur(22px) saturate(1.35) !important;
  -webkit-backdrop-filter: blur(22px) saturate(1.35) !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-btn_new_chat) [data-testid="column"] {
  display: flex !important;
  align-items: center !important;
}

[data-testid="stHorizontalBlock"]:has(.st-key-btn_new_chat) [data-testid="column"]:last-child {
  justify-content: flex-end !important;
}

/* Sağ Panel Üst Başlık Çubuğu */
.panel-bar-standalone {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.15rem;
  background: rgba(31, 36, 18, 0.25);
  border: 1px solid rgba(246, 239, 224, 0.28);
  border-bottom: 1px solid rgba(246, 239, 224, 0.16);
  border-radius: var(--panel-radius) var(--panel-radius) 0 0;
  min-height: 3.5rem;
  box-sizing: border-box;
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
}

.panel-bar-left {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.panel-glyph {
  color: var(--apricot);
  font-size: 1.1rem;
  text-shadow: 0 0 12px rgba(254, 198, 124, 0.7);
}

.panel-title {
  font-family: "Bodoni Moda", serif;
  font-style: italic;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 1.02rem;
  color: var(--paper);
}

.panel-sub {
  font-size: 0.82rem;
  color: var(--muted);
}

/* Yeni Sohbet Butonu (Beyaz Arka Plan, Sağ Üst) */
div[data-testid="stElementContainer"]:has(.st-key-btn_new_chat),
.st-key-btn_new_chat {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: center !important;
  margin: 0 !important;
  padding: 0 !important;
}

.st-key-btn_new_chat div.stButton > button,
div[data-testid="stElementContainer"]:has(.st-key-btn_new_chat) button {
  background: #FFFFFF !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(246, 239, 224, 0.8) !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.02em !important;
  padding: 0.35rem 0.95rem !important;
  border-radius: 10px !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.16) !important;
  transition: all 0.2s ease !important;
  min-height: 2.15rem !important;
  height: 2.15rem !important;
  white-space: nowrap !important;
}

.st-key-btn_new_chat div.stButton > button:hover,
div[data-testid="stElementContainer"]:has(.st-key-btn_new_chat) button:hover {
  background: #F6EFE0 !important;
  color: #38431e !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.24) !important;
}

/* Chat İçerik Alanı */
.chat-thread {
  height: calc(100vh - 21.2rem);
  min-height: 400px;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 1.1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  scroll-behavior: smooth;
  border-left: 1px solid rgba(246, 239, 224, 0.28);
  border-right: 1px solid rgba(246, 239, 224, 0.28);
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.62) 0%,
    rgba(77, 90, 46, 0.52) 55%,
    rgba(61, 70, 32, 0.58) 100%
  );
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
}

.chat-thread::-webkit-scrollbar,
.tickets-thread::-webkit-scrollbar {
  width: 7px;
}

.chat-thread::-webkit-scrollbar-thumb,
.tickets-thread::-webkit-scrollbar-thumb {
  background: linear-gradient(#C4BA65, #FC9C51);
  border-radius: 99px;
}

.bubble-row {
  display: flex;
  width: 100%;
}

.bubble-row.user {
  justify-content: flex-end;
}

.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: min(88%, 32rem);
  padding: 0.9rem 1.15rem;
  border-radius: 18px;
  line-height: 1.5;
  font-size: 0.93rem;
  box-shadow: 0 4px 14px rgba(31, 36, 18, 0.16);
  word-break: break-word;
}

.bubble.user {
  background: linear-gradient(135deg, #FC9C51 0%, #E9767F 58%, #A16A84 140%);
  color: var(--paper);
  border-bottom-right-radius: 4px;
  box-shadow: 0 8px 20px rgba(233, 118, 127, 0.28);
}

.bubble.assistant {
  background: linear-gradient(
    160deg,
    rgba(254, 198, 124, 0.34) 0%,
    rgba(196, 186, 101, 0.4) 52%,
    rgba(138, 140, 65, 0.36) 100%
  );
  color: var(--cream);
  border: 1px solid rgba(254, 198, 124, 0.38);
  border-bottom-left-radius: 4px;
  backdrop-filter: blur(12px) saturate(1.15);
  -webkit-backdrop-filter: blur(12px) saturate(1.15);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    0 8px 18px rgba(77, 90, 46, 0.16);
}

.bubble-meta {
  font-size: 0.76rem;
  letter-spacing: 0.02em;
  color: var(--apricot);
  margin-top: 0.5rem;
  padding-top: 0.4rem;
  border-top: 1px dashed rgba(254, 198, 124, 0.35);
  opacity: 0.95;
  line-height: 1.35;
}

/* Chat Input Bar (Form) - Uyumlu Renkler & Estetik */
[data-testid="stForm"] {
  border: 1px solid rgba(246, 239, 224, 0.28) !important;
  border-top: 1px solid rgba(246, 239, 224, 0.16) !important;
  border-radius: 0 0 var(--panel-radius) var(--panel-radius) !important;
  background: linear-gradient(
    180deg,
    rgba(77, 90, 46, 0.58),
    rgba(61, 70, 32, 0.68)
  ) !important;
  backdrop-filter: blur(22px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(22px) saturate(1.3) !important;
  padding: 0.75rem 0.95rem !important;
  margin: 0 !important;
  box-shadow: 0 18px 50px rgba(77, 90, 46, 0.22) !important;
}

[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  gap: 0.55rem !important;
}

/* Metin Giriş Kutusu (Warm Glass Apricot Tint) */
[data-testid="stForm"] [data-testid="stTextInput"] > div > div {
  background: rgba(254, 198, 124, 0.24) !important;
  border: 1.5px solid rgba(254, 198, 124, 0.45) !important;
  border-radius: 14px !important;
  box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.12) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] > div > div:focus-within {
  border-color: rgba(254, 198, 124, 0.9) !important;
  box-shadow: 0 0 14px rgba(254, 198, 124, 0.45) !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] input {
  background: transparent !important;
  color: #F4EAD4 !important;
  font-family: "Figtree", sans-serif !important;
  font-size: 0.95rem !important;
  padding: 0.7rem 1rem !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
  color: rgba(244, 234, 212, 0.65) !important;
  font-style: italic !important;
}

/* Mesaj Gönder Butonu (Warm Gradient: Orange -> Salmon) */
[data-testid="stForm"] div.stButton > button,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] button[kind="primaryFormSubmit"],
[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
  background: linear-gradient(135deg, #FC9C51 0%, #E9767F 100%) !important;
  color: #F3EBE0 !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  border-radius: 14px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 0.7rem 1.15rem !important;
  min-height: 2.75rem !important;
  height: 2.75rem !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 4px 16px rgba(233, 118, 127, 0.38) !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
}

[data-testid="stForm"] div.stButton > button:hover,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
  transform: translateY(-1px) scale(1.02) !important;
  box-shadow: 0 6px 20px rgba(233, 118, 127, 0.55) !important;
  background: linear-gradient(135deg, #FDAB6B 0%, #ED868E 100%) !important;
}

/* Kayıtlar (Tickets) Alanı */
.tickets-thread {
  height: calc(100vh - 16.6rem);
  min-height: 480px;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0.95rem 1.05rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  border: 1px solid rgba(246, 239, 224, 0.28);
  border-top: 0;
  border-radius: 0 0 var(--panel-radius) var(--panel-radius);
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.62) 0%,
    rgba(77, 90, 46, 0.52) 55%,
    rgba(61, 70, 32, 0.58) 100%
  );
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  box-shadow:
    0 18px 50px rgba(77, 90, 46, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.record-empty {
  padding: 2.5rem 1.2rem;
  text-align: center;
  color: var(--paper);
  opacity: 0.82;
  font-size: 0.95rem;
  line-height: 1.6;
}

.ticket-card {
  background: rgba(31, 36, 18, 0.35);
  border: 1px solid rgba(246, 239, 224, 0.22);
  border-radius: 16px;
  padding: 1rem 1.15rem;
  color: var(--cream);
  backdrop-filter: blur(8px);
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.ticket-card:hover {
  border-color: rgba(254, 198, 124, 0.45);
  transform: translateY(-1px);
}

.ticket-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.45rem;
}

.ticket-id {
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--apricot);
}

.ticket-badges {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.badge-status {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.18rem 0.55rem;
  border-radius: 99px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.badge-status.open {
  background: rgba(233, 118, 127, 0.22);
  color: #F9BDB0;
  border: 1px solid rgba(233, 118, 127, 0.45);
}

.badge-status.in_progress {
  background: rgba(254, 198, 124, 0.22);
  color: #FEC67C;
  border: 1px solid rgba(254, 198, 124, 0.45);
}

.badge-status.resolved,
.badge-status.accepted {
  background: rgba(138, 140, 65, 0.3);
  color: #C4BA65;
  border: 1px solid rgba(138, 140, 65, 0.5);
}

.badge-urgency {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.18rem 0.5rem;
  border-radius: 99px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(246, 239, 224, 0.15);
}

.badge-urgency.high { color: #E9767F; }
.badge-urgency.medium { color: #FEC67C; }
.badge-urgency.low { color: #C4BA65; }

.ticket-title {
  font-family: "Bodoni Moda", serif;
  font-style: italic;
  font-size: 1.12rem;
  color: var(--paper);
  margin: 0.2rem 0 0.4rem 0;
  line-height: 1.25;
}

.ticket-path {
  font-size: 0.78rem;
  color: var(--muted);
  margin-bottom: 0.6rem;
  line-height: 1.35;
}

.ticket-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.4rem 0.8rem;
  font-size: 0.82rem;
  padding-top: 0.45rem;
  border-top: 1px solid rgba(246, 239, 224, 0.12);
}

.ticket-grid-item {
  color: var(--sand);
}

.ticket-grid-item strong {
  color: var(--paper);
}

.ticket-ask {
  margin-top: 0.55rem;
  font-size: 0.82rem;
  font-style: italic;
  color: var(--cream);
  opacity: 0.88;
  line-height: 1.4;
  background: rgba(0, 0, 0, 0.18);
  padding: 0.4rem 0.65rem;
  border-radius: 8px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "meta": "",
            }
        ]
    if "phase" not in st.session_state:
        st.session_state.phase = "open"
    if "slots" not in st.session_state:
        st.session_state.slots = {}
    if "last_rule_id" not in st.session_state:
        st.session_state.last_rule_id = None
    if "last_ticket_id" not in st.session_state:
        st.session_state.last_ticket_id = None
    if "classification" not in st.session_state:
        st.session_state.classification = None


_init_state()


def _format_content(text: str) -> str:
    escaped = html.escape(text)
    # Bold **text** -> <strong>text</strong>
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    # Italic *text* -> <em>text</em>
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    # Newlines -> <br>
    return escaped.replace("\n", "<br>")


def _format_date(iso_str: str) -> str:
    if not iso_str:
        return "—"
    try:
        parts = iso_str.split("T")
        d_parts = parts[0].split("-")
        t_part = parts[1][:5] if len(parts) > 1 else ""
        return f"{d_parts[2]}.{d_parts[1]}.{d_parts[0]} {t_part}".strip()
    except Exception:
        return iso_str


def _status_label(status: str) -> str:
    status = (status or "open").lower()
    if status == "open":
        return "Açık"
    if status == "in_progress":
        return "İnceleniyor"
    if status in {"resolved", "accepted"}:
        return "Çözüldü"
    return status.title()


def _urgency_label(urgency: str) -> str:
    urgency = (urgency or "medium").lower()
    if urgency == "high":
        return "Yüksek Öncelik"
    if urgency == "low":
        return "Düşük Öncelik"
    return "Orta Öncelik"


def _handle_send():
    user_input = st.session_state.get("chat_input_text", "").strip()
    if not user_input:
        return

    # Add user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input, "meta": ""}
    )

    # Convert session history
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # Run orchestrator
    result = handle_turn(
        user_input,
        history=history,
        phase=st.session_state.phase,
        last_rule_id=st.session_state.last_rule_id,
        last_ticket_id=st.session_state.last_ticket_id,
        slots=st.session_state.slots,
        classification=st.session_state.classification,
    )

    # Update states
    st.session_state.phase = result.phase
    st.session_state.last_rule_id = result.last_rule_id
    st.session_state.slots = result.slots or {}
    st.session_state.classification = result.classification

    if result.ticket:
        st.session_state.last_ticket_id = result.ticket["id"]
    elif result.debug.get("action") == "resolved":
        st.session_state.last_ticket_id = None

    # Meta text (sınıflandırma bilgisi)
    meta_line = ""
    if result.classification and result.classification.get("path_label"):
        meta_line = f"🏷️ Sınıf: {result.classification['path_label']}"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.reply,
            "meta": meta_line,
        }
    )

    # Clear input
    st.session_state.chat_input_text = ""


def _reset_chat():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "meta": "",
        }
    ]
    st.session_state.phase = "open"
    st.session_state.slots = {}
    st.session_state.last_rule_id = None
    st.session_state.last_ticket_id = None
    st.session_state.classification = None
    st.session_state.chat_input_text = ""


# -------------------------------------------------------------
# Sayfa Üst Başlığı
# -------------------------------------------------------------
st.markdown(
    """
<div class="page-head">
  <h1 class="page-title">ITSM Asistanı</h1>
  <p class="page-sub">Kurum içi destek asistanı. Talebi doğal dille alır, sınıflandırır, geçmiş çözümlerden önerir ve gerektiğinde kayıt açar.</p>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# İki Kolonlu Panel Düzeni
# -------------------------------------------------------------
col_chat, col_tickets = st.columns([1, 1], gap="medium")

# =============================================================
# SOL KUTUCUK: Asistan ile Sohbet
# =============================================================
with col_chat:
    # Header bar: Sol tarafta başlık, Sağ tarafta beyaz "Yeni Sohbet" butonu
    head_left, head_right = st.columns([3.3, 1.3], gap="small")
    with head_left:
        st.markdown(
            """
<div class="panel-bar-left">
  <span class="panel-glyph">✦</span>
  <span class="panel-title">Asistan</span>
  <span class="panel-sub">· Doğal dil desteği</span>
</div>
""",
            unsafe_allow_html=True,
        )
    with head_right:
        st.button(
            "Yeni Sohbet",
            key="btn_new_chat",
            on_click=_reset_chat,
            use_container_width=True,
        )

    # Messages HTML Thread
    msg_html_list = []
    for msg in st.session_state.messages:
        role = msg["role"]
        formatted_text = _format_content(msg["content"])
        meta_html = ""
        if msg.get("meta"):
            meta_html = f'<div class="bubble-meta">{html.escape(msg["meta"])}</div>'

        bubble_html = (
            f'<div class="bubble-row {role}">'
            f'  <div class="bubble {role}">'
            f'    {formatted_text}'
            f"    {meta_html}"
            f"  </div>"
            f"</div>"
        )
        msg_html_list.append(bubble_html)

    thread_body = "\n".join(msg_html_list)
    st.markdown(
        f"""
<div class="chat-thread" id="chatThread">
  {thread_body}
</div>
<script>
  var el = document.getElementById("chatThread");
  if (el) {{ el.scrollTop = el.scrollHeight; }}
</script>
""",
        unsafe_allow_html=True,
    )

    # Form with text input and submit button (warm gradient send button)
    with st.form("chat_form", clear_on_submit=True):
        form_cols = st.columns([5.5, 1.5], gap="small")
        with form_cols[0]:
            st.text_input(
                "Mesaj",
                placeholder="Talebinizi veya sorununuzu yazın...",
                key="chat_input_text",
                label_visibility="collapsed",
            )
        with form_cols[1]:
            st.form_submit_button("Gönder ➤", on_click=_handle_send, use_container_width=True)


# =============================================================
# SAĞ KUTUCUK: Kayıtlar (Tickets)
# =============================================================
with col_tickets:
    all_tickets = load_tickets()
    ticket_count = len(all_tickets)

    # Header bar
    st.markdown(
        f"""
<div class="panel-bar-standalone">
  <div class="panel-bar-left">
    <span class="panel-glyph">✦</span>
    <span class="panel-title">Kayıtlar</span>
    <span class="panel-sub">· {ticket_count} kayıt</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not all_tickets:
        tickets_body = """
<div class="record-empty">
  Henüz açık veya oluşturulmuş bir kayıt yok.<br><br>
  Asistanla sohbet ederek arıza, erişim veya hizmet talebi oluşturduğunuzda kayıtlar burada listelenecektir.
</div>
"""
    else:
        cards_html = []
        for t in reversed(all_tickets):
            tid = html.escape(str(t.get("id") or "T-XXXX"))
            status = str(t.get("status") or "open").lower()
            status_text = _status_label(status)
            urgency = str(t.get("urgency") or "medium").lower()
            urgency_text = _urgency_label(urgency)

            title = str(
                t.get("surec_label")
                or t.get("modul_label")
                or t.get("category")
                or "Destek Kaydı"
            )
            title = html.escape(title)

            path = str(
                t.get("path_label")
                or t.get("talep_turu_label")
                or t.get("category")
                or "—"
            )
            path = html.escape(path)

            date_str = _format_date(str(t.get("created_at") or ""))
            asset = html.escape(str(t.get("asset") or "—"))
            location = html.escape(str(t.get("location") or "—"))
            impact = html.escape(str(t.get("impact") or "—"))

            ask_text = str(t.get("customer_ask") or "").strip()
            ask_html = ""
            if ask_text:
                ask_html = f'<div class="ticket-ask">"{html.escape(ask_text)}"</div>'

            card = f"""
<div class="ticket-card">
  <div class="ticket-card-header">
    <span class="ticket-id">{tid}</span>
    <div class="ticket-badges">
      <span class="badge-status {status}">{status_text}</span>
      <span class="badge-urgency {urgency}">{urgency_text}</span>
    </div>
  </div>
  <div class="ticket-title">{title}</div>
  <div class="ticket-path">📍 {path}</div>
  <div class="ticket-grid">
    <div class="ticket-grid-item"><strong>Varlık:</strong> {asset}</div>
    <div class="ticket-grid-item"><strong>Konum:</strong> {location}</div>
    <div class="ticket-grid-item"><strong>Etki:</strong> {impact}</div>
    <div class="ticket-grid-item"><strong>Tarih:</strong> {date_str}</div>
  </div>
  {ask_html}
</div>
"""
            cards_html.append(card)
        tickets_body = "\n".join(cards_html)

    st.markdown(
        f"""
<div class="tickets-thread">
  {tickets_body}
</div>
""",
        unsafe_allow_html=True,
    )
