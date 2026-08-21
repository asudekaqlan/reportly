"""
ITSM Asistanı — Streamlit UI
Run from the project root:
    streamlit run src/app.py
"""

import base64
import html
import re
import uuid
from pathlib import Path

import streamlit as st

from auth import (
    authenticate,
    captcha_matches,
    ensure_default_admin,
    find_user,
    is_valid_email,
    password_checks,
    password_issues,
    random_captcha,
    random_email_code,
    register_user,
)
from reports import load_jobs
from orchestrator import handle_turn
from taxonomy import classify_request  # loaded with the UI so Streamlit picks up classifier changes
from tickets import load_tickets, tickets_for_customer, update_status

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

WELCOME = (
    "Merhaba, ben ITSM asistanın. "
    "Talebini doğal dille yaz; sınıflandırır, varsa çözüm kaydı öneririm, "
    "gerekirse eksik alanları tamamlayıp ticket açarım.\n\n"
    "Örneğin: *Bilgisayarım bozuldu, talep açmak istiyorum.*"
)

CONSENT_TEXT = (
    "Hesap açarak adımın, soyadımın ve e-posta adresimin hesap açmak, "
    "oturumu doğrulamak ve ITSM taleplerimi izlemek için işlenmesini kabul ederim. "
    "Bu onayı dilediğim zaman geri çekebilirim."
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
  overflow: hidden !important;
  max-width: 100%;
  width: 100%;
  height: 100% !important;
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
  overflow: hidden !important;
  width: 100% !important;
  max-width: 100% !important;
  height: 100% !important;
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
[data-testid="stToolbar"] { display: none; }
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
  padding-top: 1.05rem !important;
  padding-bottom: 1.05rem !important;
  padding-left: clamp(1.1rem, 3.2vw, 2.1rem) !important;
  padding-right: clamp(1.1rem, 3.2vw, 2.1rem) !important;
  max-width: min(1280px, 100%);
  overflow: hidden !important;
  min-height: 100vh !important;
  max-height: 100vh !important;
  box-sizing: border-box !important;
}

/* Başlık Alanı */
.page-head {
  margin: 0 0 1.15rem 0 !important;
  text-align: left;
}
.page-title {
  font-family: "Bodoni Moda", serif !important;
  font-style: italic !important;
  font-weight: 700 !important;
  font-size: clamp(2.35rem, 4.8vw, 3.4rem) !important;
  line-height: 1.08;
  letter-spacing: 0.01em;
  text-transform: none;
  color: var(--paper);
  margin: 0 !important;
  text-align: left !important;
}
.page-sub {
  margin: 0.35rem 0 0 0 !important;
  color: var(--paper);
  opacity: 0.82;
  font-family: "Figtree", sans-serif;
  font-style: italic;
  font-size: 0.94rem;
  font-weight: 300;
  line-height: 1.45;
  letter-spacing: 0.01em;
  max-width: 44rem;
}
div[data-testid="stMarkdownContainer"]:has(.page-head) {
  text-align: left !important;
}

/* Streamlit başlık anchor/bağlantı ikonunu gizle */
[data-testid="stHeaderActionElements"],
.anchor-link,
a.header-anchor,
.page-title a,
.page-head a,
a[href*="#itsm-asistani"] {
  display: none !important;
  visibility: hidden !important;
  pointer-events: none !important;
}

/* Çalışma Alanı ve İki Ana Panel */
.st-key-workspace {
  border: 0 !important;
  background: transparent !important;
  padding: 0 !important;
  margin: 0 !important;
}
.st-key-workspace [data-testid="stHorizontalBlock"] {
  align-items: stretch !important;
  gap: 1.25rem !important;
}
.st-key-workspace [data-testid="column"],
.st-key-workspace [data-testid="stColumn"],
.st-key-workspace [data-testid="stHorizontalBlock"] > div {
  min-width: 0 !important;
}
.st-key-workspace [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-chat_shell),
.st-key-workspace [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-tickets_pane),
.st-key-workspace .stElementContainer:has(.st-key-chat_shell),
.st-key-workspace .stElementContainer:has(.st-key-tickets_pane) {
  height: calc(100vh - 14.8rem) !important;
  min-height: 20rem !important;
}

.st-key-chat_shell,
.st-key-tickets_pane {
  position: relative !important;
  width: 100% !important;
  height: calc(100vh - 14.8rem) !important;
  min-height: 20rem !important;
  margin: 0 !important;
  padding: 0 !important;
  border-radius: var(--panel-radius) !important;
  border: 1px solid rgba(246, 239, 224, 0.28) !important;
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.62) 0%,
    rgba(77, 90, 46, 0.52) 55%,
    rgba(61, 70, 32, 0.58) 100%
  ) !important;
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  box-shadow:
    0 18px 50px rgba(77, 90, 46, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}
.st-key-chat_shell {
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.st-key-tickets_pane {
  overflow-x: hidden !important;
  overflow-y: auto !important;
  padding: 0 0 0.85rem !important;
  box-sizing: border-box !important;
}

/* Chat Shell İç Düzen */
.st-key-chat_shell [data-testid="stVerticalBlock"],
.st-key-chat_shell [data-testid="stHorizontalBlock"] {
  gap: 0 !important;
  row-gap: 0 !important;
}
.st-key-chat_shell [data-testid="stElementContainer"],
.st-key-chat_shell .stElementContainer,
.st-key-chat_shell [data-testid="stVerticalBlockBorderWrapper"] {
  margin: 0 !important;
  padding: 0 !important;
}

.chat-panel {
  position: relative;
  margin: 0;
  width: 100%;
  border-radius: 0;
  overflow: hidden;
  color: var(--cream);
  background: transparent;
  border: 0;
  box-shadow: none;
}

.chat-bar,
.tickets-bar {
  display: flex;
  align-items: center;
  gap: 0.65em;
  padding: 0.85em 1.1em;
  border-bottom: 1px solid rgba(246, 239, 224, 0.16);
  background: linear-gradient(90deg, rgba(196, 186, 101, 0.18), rgba(254, 198, 124, 0.1));
  min-width: 0;
}
.tickets-bar {
  padding: 0.85em 5.6rem 0.85em 1.1em;
  margin: 0 0 0.55rem 0;
}

.spark {
  color: var(--apricot);
  font-size: 1.05em;
  text-shadow: 0 0 12px rgba(254, 198, 124, 0.7);
}
.chat-bar-title {
  font-family: "Bodoni Moda", serif;
  font-style: italic;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 1em;
}
.chat-bar-sub {
  font-size: 0.78em;
  color: var(--muted);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.new-chat {
  margin-left: auto;
  color: #4D5A2E !important;
  background: var(--paper);
  text-decoration: none !important;
  text-transform: lowercase;
  box-shadow: 0 2px 10px rgba(77, 90, 46, 0.18);
  font-size: 0.82em;
  font-weight: 650;
  letter-spacing: 0.02em;
  white-space: nowrap;
  padding: 0.38em 0.78em;
  border-radius: 10px;
}
.new-chat:hover {
  color: #3d4824 !important;
  background: var(--paper);
  opacity: 1;
}

.chat-thread {
  height: calc(100vh - 22.0rem);
  min-height: 10rem;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 1.1em 1em 1.2em;
  display: flex;
  flex-direction: column;
  gap: 0.75em;
}
.chat-thread::-webkit-scrollbar { width: 8px; }
.chat-thread::-webkit-scrollbar-thumb {
  background: linear-gradient(#C4BA65, #FC9C51);
  border-radius: 99px;
}

.bubble-row { display: flex; }
.bubble-row.user { justify-content: flex-end; }
.bubble-row.assistant { justify-content: flex-start; }

.bubble {
  max-width: min(88%, 34rem);
  padding: 0.9em 1.15em;
  border-radius: 18px;
  line-height: 1.5;
  font-size: 0.92rem;
  box-shadow: 0 4px 14px rgba(31, 36, 18, 0.16);
  word-break: break-word;
}
.bubble.user {
  background: linear-gradient(135deg, #FC9C51 0%, #E9767F 58%, #A16A84 140%);
  color: var(--paper);
  border-bottom-right-radius: 6px;
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
  border-bottom-left-radius: 6px;
  backdrop-filter: blur(12px) saturate(1.15);
  -webkit-backdrop-filter: blur(12px) saturate(1.15);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    0 8px 18px rgba(77, 90, 46, 0.16);
}
.bubble-meta {
  font-size: 0.72em;
  letter-spacing: 0.02em;
  color: var(--apricot);
  margin-top: 0.45em;
  opacity: 0.95;
  overflow-wrap: anywhere;
}
.bubble.typing {
  display: flex;
  align-items: center;
  gap: 0.35em;
  min-width: 3.2em;
  padding: 0.85em 1em;
}
.bubble.typing span {
  width: 0.42em;
  height: 0.42em;
  border-radius: 50%;
  background: var(--apricot);
  opacity: 0.45;
  animation: typing-dot 1.1s ease-in-out infinite;
}
.bubble.typing span:nth-child(2) { animation-delay: 0.16s; }
.bubble.typing span:nth-child(3) { animation-delay: 0.32s; }
@keyframes typing-dot {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.35; }
  40% { transform: translateY(-0.22em); opacity: 0.95; }
}

/* Kayıt Kartları ve Listesi */
.record-empty {
  padding: 0.85rem 1.1rem 1rem !important;
  margin: 0 !important;
  color: var(--paper);
  opacity: 0.88;
  font-size: 0.94rem;
  line-height: 1.55;
  text-align: left !important;
}

.st-key-tickets_pane .ticket-card {
  margin: 0.55rem 0.9rem 0;
  padding: 0.85rem 0.95rem;
}
.ticket-card {
  color: var(--cream);
  border-radius: 18px;
  padding: 1.15rem 1.25rem;
  margin-top: 0.6rem;
}
.ticket-kicker {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--apricot);
}
.ticket-title {
  font-family: "Bodoni Moda", serif;
  font-style: italic;
  font-size: 1.15rem;
  margin: 0.2rem 0 0.45rem 0;
}
.ticket-meta {
  color: var(--muted);
  font-size: 0.92rem;
  margin-bottom: 0.8rem;
}
.ticket-card ul { margin: 0.2rem 0 0.8rem 1.1rem; }
.ticket-card li { margin: 0.2rem 0; }
.handoff {
  white-space: pre-wrap;
  background: rgba(31, 36, 18, 0.35);
  border: 1px solid rgba(246, 239, 224, 0.18);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  font-size: 0.92rem;
  line-height: 1.45;
}
.urgency-high { color: #E9767F; font-weight: 600; }
.urgency-medium { color: #FEC67C; font-weight: 600; }
.urgency-low { color: #C4BA65; font-weight: 600; }

.st-key-tickets_pane .st-key-tickets_login,
.st-key-tickets_pane .st-key-tickets_logout {
  position: absolute !important;
  top: 0.62rem;
  right: 0.75rem;
  width: auto !important;
  z-index: 3;
}
.st-key-tickets_pane [data-testid="stElementContainer"]:has(.st-key-tickets_login),
.st-key-tickets_pane [data-testid="stElementContainer"]:has(.st-key-tickets_logout),
.st-key-tickets_pane .stElementContainer:has(.st-key-tickets_login),
.st-key-tickets_pane .stElementContainer:has(.st-key-tickets_logout) {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  border: 0 !important;
}
.st-key-tickets_pane div.stButton > button {
  background: var(--paper) !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(246, 239, 224, 0.45) !important;
  min-height: 2.05rem !important;
  height: 2.05rem !important;
  padding: 0 0.85rem !important;
  font-size: 0.82rem !important;
  box-shadow: 0 2px 10px rgba(77, 90, 46, 0.16) !important;
}

/* Genel Buton Stilleri */
div.stButton > button {
  background: linear-gradient(135deg, #5E5C2D, #4D5A2E) !important;
  color: var(--cream) !important;
  border: 1px solid rgba(246, 239, 224, 0.28) !important;
  border-radius: 12px !important;
  font-weight: 650 !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 22px rgba(77, 90, 46, 0.28) !important;
}
div.stButton > button:hover {
  background: linear-gradient(135deg, #FC9C51, #E9767F) !important;
  color: var(--paper) !important;
}

/* Chat Mesaj Giriş Formu */
[data-testid="stForm"] {
  border: 0 !important;
  border-top: 1px solid rgba(246, 239, 224, 0.16) !important;
  border-radius: 0 0 var(--panel-radius) var(--panel-radius) !important;
  background: linear-gradient(
    180deg,
    rgba(77, 90, 46, 0.5),
    rgba(61, 70, 32, 0.58)
  ) !important;
  backdrop-filter: blur(22px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(22px) saturate(1.3) !important;
  padding: 0.85rem 0.9rem 0.95rem !important;
  margin: 0 !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
}

[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  gap: 0.35rem !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] {
  width: 100% !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input,
[data-testid="stForm"] [data-testid="stTextInput"] > div > div {
  background: rgba(254, 198, 124, 0.25) !important;
  color: var(--cream) !important;
  border: 1px solid rgba(254, 198, 124, 0.38) !important;
  border-radius: 16px !important;
  min-height: 2.55rem !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input:focus {
  border-color: rgba(254, 198, 124, 0.7) !important;
}

[data-testid="stForm"] div.stButton > button,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] button[kind="formSubmit"],
[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
  background: none !important;
  color: var(--paper) !important;
  font-size: 1.6rem !important;
  box-shadow: none !important;
  border: 0 !important;
}

/* Auth / Giriş Dialogları */
.captcha-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.28rem;
  min-height: 3.1rem;
  border-radius: 12px;
  background:
    repeating-linear-gradient(-18deg, rgba(77,90,46,.08) 0 8px, transparent 8px 16px),
    linear-gradient(180deg, #F6EFE0, #E7D9B8);
  border: 1px solid rgba(77, 90, 46, 0.28);
  letter-spacing: 0.28em;
  font-family: "Calfine", serif;
  font-size: 1.45rem;
  color: #3d4824;
  user-select: none;
}
.pw-checks {
  list-style: none;
  padding: 0;
  margin: 0.15rem 0 0.7rem;
  font-size: 0.82rem;
}
.pw-checks li { margin: 0.12rem 0; color: #8A6A4A; }
.pw-checks li.ok { color: #4D5A2E; }
.consent-copy {
  font-size: 0.86rem;
  line-height: 1.45;
  color: var(--olive);
  background: rgba(243, 235, 224, 0.72);
  border: 1px solid rgba(77, 90, 46, 0.18);
  border-radius: 10px;
  padding: 0.7rem 0.8rem;
  margin: 0.2rem 0 0.55rem;
}
.st-key-admin_entry_btn button,
[data-testid="stDialog"] .st-key-admin_entry_btn button,
div[role="dialog"] .st-key-admin_entry_btn button {
  background: none !important;
  color: rgba(77, 90, 46, 0.4) !important;
  border: 0 !important;
  box-shadow: none !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
}
.st-key-admin_entry_btn button:hover,
[data-testid="stDialog"] .st-key-admin_entry_btn button:hover,
div[role="dialog"] .st-key-admin_entry_btn button:hover {
  background: none !important;
  color: rgba(77, 90, 46, 0.72) !important;
}
.st-key-admin_back_btn button {
  background: none !important;
  color: var(--olive) !important;
  border: 0 !important;
  box-shadow: none !important;
}
.admin-kicker {
  font-size: 0.75rem;
  font-weight: 650;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--apricot);
  margin-bottom: 0.35rem;
}

div[role="dialog"] [data-testid="stWidgetLabel"] p { color: var(--olive) !important; }
div[role="dialog"] [data-testid="stTextInput"] input,
div[role="dialog"] [data-testid="stTextInput"] > div > div {
  background: var(--paper) !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(77, 90, 46, 0.18) !important;
  border-radius: 12px !important;
}

/* Yönetici / Hero Görünümü */
.hero {
  text-align: center;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
div[data-testid="stMarkdownContainer"]:has(.hero) {
  width: 100% !important;
  text-align: center !important;
}
.lede, p.lede {
  font-size: clamp(0.88rem, 0.75rem + 1.1vw, 1.02rem);
  line-height: 1.55;
  color: var(--paper);
  max-width: 44rem;
  margin: 0 auto 0.4rem auto !important;
  text-align: center !important;
}

[data-testid="stAlert"] {
  background: rgba(77, 90, 46, 0.55) !important;
  color: var(--cream) !important;
  border: 1px solid rgba(254, 198, 124, 0.4) !important;
  backdrop-filter: blur(16px);
}
[data-testid="stWidgetLabel"] p { color: var(--olive) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: rgba(77, 90, 46, 0.55) !important;
  color: var(--cream) !important;
  border-color: rgba(246, 239, 224, 0.28) !important;
}

/* Mobil / Responsive Düzen */
@media (max-width: 860px) {
  html, body, .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  section.main {
    overflow-x: hidden !important;
    overflow-y: auto !important;
    height: auto !important;
  }
  .block-container,
  [data-testid="stMainBlockContainer"] {
    overflow: visible !important;
    min-height: auto !important;
    max-height: none !important;
  }
  .st-key-workspace [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 1rem !important;
  }
  .st-key-chat_shell,
  .st-key-tickets_pane,
  .st-key-workspace [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-chat_shell),
  .st-key-workspace [data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-tickets_pane) {
    height: 28rem !important;
  }
  .chat-thread {
    height: 19rem !important;
  }
  .chat-bar-sub { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .bubble.typing span { animation: none; opacity: 0.7; }
}
</style>
"""


def _blank_conversation() -> dict:
    return {
        "id": uuid.uuid4().hex[:10],
        "title": "Yeni sohbet",
        "messages": [{"role": "assistant", "content": WELCOME}],
        "phase": "open",
        "last_rule_id": None,
        "last_ticket_id": None,
        "last_debug": None,
        "pending_prompt": None,
        "slots": {},
        "classification": None,
    }


def _current_conversation() -> dict:
    cid = st.session_state.current_conv_id
    for conv in st.session_state.conversations:
        if conv["id"] == cid:
            return conv
    conv = st.session_state.conversations[0]
    st.session_state.current_conv_id = conv["id"]
    return conv


def _bind_conversation(conv: dict) -> None:
    st.session_state.current_conv_id = conv["id"]
    st.session_state.messages = conv["messages"]
    st.session_state.phase = conv["phase"]
    st.session_state.last_rule_id = conv["last_rule_id"]
    st.session_state.last_ticket_id = conv["last_ticket_id"]
    st.session_state.last_debug = conv["last_debug"]
    st.session_state.pending_prompt = conv.get("pending_prompt")
    st.session_state.slots = dict(conv.get("slots") or {})
    st.session_state.classification = conv.get("classification")


def _sync_conversation() -> None:
    conv = _current_conversation()
    conv["messages"] = st.session_state.messages
    conv["phase"] = st.session_state.phase
    conv["last_rule_id"] = st.session_state.last_rule_id
    conv["last_ticket_id"] = st.session_state.last_ticket_id
    conv["last_debug"] = st.session_state.last_debug
    conv["pending_prompt"] = st.session_state.get("pending_prompt")
    conv["slots"] = dict(st.session_state.get("slots") or {})
    conv["classification"] = st.session_state.get("classification")
    first_user = next(
        (item.get("content") for item in conv["messages"] if item.get("role") == "user"),
        None,
    )
    if first_user:
        conv["title"] = " ".join(str(first_user).split())[:42]


def _init_state():
    if "conversations" not in st.session_state:
        first = _blank_conversation()
        if st.session_state.get("messages"):
            first["messages"] = st.session_state.messages
            first["phase"] = st.session_state.get("phase", "open")
            first["last_rule_id"] = st.session_state.get("last_rule_id")
            first["last_ticket_id"] = st.session_state.get("last_ticket_id")
            first["last_debug"] = st.session_state.get("last_debug")
            first["pending_prompt"] = st.session_state.get("pending_prompt")
        st.session_state.conversations = [first]
        st.session_state.current_conv_id = first["id"]
        _bind_conversation(first)
    elif "messages" not in st.session_state:
        _bind_conversation(_current_conversation())
    st.session_state.setdefault("phase", "open")
    st.session_state.setdefault("last_rule_id", None)
    st.session_state.setdefault("last_ticket_id", None)
    st.session_state.setdefault("last_debug", None)
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("slots", {})
    st.session_state.setdefault("classification", None)
    st.session_state.setdefault("captcha_field_key", 0)
    st.session_state.setdefault("auth_open", False)
    st.session_state.setdefault("auth_mode", "login")
    st.session_state.setdefault("auth_error", "")
    st.session_state.setdefault("pending_registration", None)
    st.session_state.setdefault("chat_drawer_open", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("my_ticket_ids", [])
    st.session_state.setdefault("customer_view", "chat")
    if not st.session_state.get("captcha_answer"):
        st.session_state.captcha_answer = random_captcha()
    ensure_default_admin()


def _reset_chat():
    current = _current_conversation()
    has_user = any(item.get("role") == "user" for item in current.get("messages") or [])
    if not has_user:
        _bind_conversation(current)
        return
    conv = _blank_conversation()
    st.session_state.conversations.append(conv)
    _bind_conversation(conv)


def _refresh_captcha() -> None:
    st.session_state.captcha_answer = random_captcha()
    st.session_state.captcha_field_key = st.session_state.get("captcha_field_key", 0) + 1


def _debug_line(debug: dict | None) -> str:
    if not debug:
        return ""
    action = debug.get("action") or "—"
    return (
        f"{debug.get('talep_turu', '—')} → {debug.get('birim', '—')} → "
        f"{debug.get('modul', '—')} → {debug.get('surec', '—')} · "
        f"üslup: {debug.get('sentiment', '—')} · eylem: {action}"
    )


def _esc(value: object) -> str:
    return html.escape(str(value or ""))


def _format_text(text: str) -> str:
    escaped = html.escape(text or "")
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped.replace("\n", "<br>")


def _format_tr_date(iso_value: str) -> str:
    raw = str(iso_value or "").strip()
    parts = raw.split("-")
    if len(parts) == 3 and all(parts):
        return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return raw


def _messages_html(
    messages: list[dict],
    typing: bool = False,
    picker_html: str = "",
) -> str:
    last_assistant = -1
    for index, message in enumerate(messages):
        if message.get("role") != "user":
            last_assistant = index
    panel_class = "chat-panel glass"
    parts = [
        f"""
        <div class="{panel_class}">
          <div class="chat-bar">
            <span class="spark">✦</span>
            <span class="chat-bar-title">Sohbet</span>
            <a class="new-chat" href="?reset=1">yeni sohbet</a>
          </div>
          <div class="chat-thread">
        """
    ]
    for index, message in enumerate(messages):
        role = message.get("role", "assistant")
        css_role = "user" if role == "user" else "assistant"
        body = _format_text(str(message.get("content", "")))
        meta = ""
        extra = ""
        bubble_class = f"bubble {css_role}"
        attach = (
            bool(picker_html)
            and not typing
            and css_role == "assistant"
            and index == last_assistant
        )
        if attach:
            extra = picker_html
            bubble_class = "bubble assistant has-orders"
        elif css_role == "assistant" and message.get("debug"):
            meta = f'<div class="bubble-meta">{html.escape(_debug_line(message["debug"]))}</div>'
        parts.append(
            f'<div class="bubble-row {css_role}">'
            f'<div class="{bubble_class}">{body}{extra}{meta}</div>'
            "</div>"
        )
    if typing:
        parts.append(
            '<div class="bubble-row assistant">'
            '<div class="bubble assistant typing"><span></span><span></span><span></span></div>'
            "</div>"
        )
    parts.append("</div></div>")
    return "".join(parts)


def _apply_turn(prompt: str) -> None:
    result = handle_turn(
        prompt,
        history=st.session_state.messages[:-1],
        phase=st.session_state.phase,
        last_rule_id=st.session_state.last_rule_id,
        last_ticket_id=st.session_state.last_ticket_id,
        customer_email=_customer_email(),
        slots=st.session_state.get("slots") or {},
        classification=st.session_state.get("classification"),
    )
    _apply_result(result)


def _apply_result(result) -> None:
    st.session_state.messages.append(
        {"role": "assistant", "content": result.reply, "debug": result.debug}
    )
    st.session_state.phase = result.phase
    st.session_state.last_rule_id = result.last_rule_id
    st.session_state.last_debug = result.debug
    if result.ticket:
        st.session_state.last_ticket_id = result.ticket["id"]
        ids = list(st.session_state.get("my_ticket_ids") or [])
        tid = result.ticket["id"]
        if tid not in ids:
            ids.append(tid)
        st.session_state.my_ticket_ids = ids
    st.session_state.slots = dict(result.slots or {})
    st.session_state.classification = result.classification
    if result.phase == "open":
        st.session_state.slots = {}
        st.session_state.classification = None
    _sync_conversation()


def _password_checklist_html(password: str) -> str:
    checks = password_checks(password)
    labels = (
        ("length", "En az 12 karakter"),
        ("upper", "En az bir büyük harf"),
        ("lower", "En az bir küçük harf"),
        ("digit", "En az bir rakam"),
        ("special", "En az bir özel karakter"),
    )
    items = []
    for key, label in labels:
        ok = checks[key]
        mark = "✓" if ok else "○"
        cls = "ok" if ok else "wait"
        items.append(f'<li class="{cls}">{mark} {_esc(label)}</li>')
    return f'<ul class="pw-checks">{"".join(items)}</ul>'


def _close_auth_dialog() -> None:
    st.session_state.auth_open = False
    st.session_state.auth_error = ""


def _render_login_panel() -> None:
    email = st.text_input("E-posta", key="login_email", placeholder="ornek@posta.com")
    password = st.text_input("Şifre", key="login_password", type="password")
    st.caption("Captcha kontrolü")
    cap_row = st.columns([3, 1])
    with cap_row[0]:
        letters = "".join(f"<span>{_esc(ch)}</span>" for ch in st.session_state.captcha_answer)
        st.markdown(f'<div class="captcha-box">{letters}</div>', unsafe_allow_html=True)
    with cap_row[1]:
        if st.button("Yenile", key="captcha_refresh", use_container_width=True):
            _refresh_captcha()
            st.rerun()
    captcha = st.text_input(
        "Görüntüdeki kodu yazın",
        key=f"login_captcha_{st.session_state.captcha_field_key}",
    )
    if st.button("Giriş", key="login_submit", use_container_width=True, type="primary"):
        if not captcha_matches(st.session_state.captcha_answer, captcha):
            st.session_state.auth_error = "Captcha doğrulaması başarısız."
            _refresh_captcha()
            st.rerun()
        user = authenticate(email, password, role="customer")
        if not user:
            st.session_state.auth_error = "E-posta veya şifre hatalı."
            _refresh_captcha()
            st.rerun()
        st.session_state.user = user
        st.session_state.auth_open = False
        st.session_state.auth_error = ""
        st.rerun()
    st.button(
        "Yönetici girişi",
        key="admin_entry_btn",
        type="tertiary",
        on_click=lambda: st.session_state.update(auth_mode="admin_login", auth_error=""),
    )


def _render_admin_login_panel() -> None:
    st.caption("Yönetici")
    email = st.text_input("E-posta", key="admin_email")
    password = st.text_input("Şifre", key="admin_password", type="password")
    if st.button("Giriş", key="admin_submit", use_container_width=True, type="primary"):
        user = authenticate(email, password, role="admin")
        if not user:
            st.session_state.auth_error = "Yönetici girişi başarısız."
            st.rerun()
        st.session_state.user = user
        st.session_state.auth_open = False
        st.session_state.auth_error = ""
        st.session_state.chat_drawer_open = False
        st.rerun()
    st.button(
        "Müşteri girişine dön",
        key="admin_back_btn",
        type="tertiary",
        on_click=lambda: st.session_state.update(auth_mode="login", auth_error=""),
    )


def _start_email_verification() -> None:
    first = (st.session_state.get("reg_first") or "").strip()
    last = (st.session_state.get("reg_last") or "").strip()
    email = (st.session_state.get("reg_email") or "").strip()
    password = st.session_state.get("reg_password") or ""
    confirm = st.session_state.get("reg_password2") or ""
    consent = bool(st.session_state.get("reg_consent"))

    if not first or not last:
        st.session_state.auth_error = "Ad ve soyad gerekli."
        return
    if not is_valid_email(email):
        st.session_state.auth_error = "Geçerli bir e-posta yazın."
        return
    if find_user(email):
        st.session_state.auth_error = "Bu e-posta ile kayıtlı bir hesap zaten var."
        return
    issues = password_issues(password)
    if issues:
        st.session_state.auth_error = " ".join(issues)
        return
    if password != confirm:
        st.session_state.auth_error = "Şifreler eşleşmiyor."
        return
    if not consent:
        st.session_state.auth_error = "Devam etmek için onay metnini kabul edin."
        return

    st.session_state.pending_registration = {
        "first_name": first,
        "last_name": last,
        "email": email,
        "password": password,
        "code": random_email_code(),
    }
    st.session_state.auth_error = ""


def _render_register_panel() -> None:
    pending = st.session_state.get("pending_registration")
    if pending:
        st.info(
            f"Doğrulama kodu {pending['email']} adresine gönderildi. "
            f"Demo kod: **{pending['code']}**"
        )
        code = st.text_input("E-posta doğrulama kodu", key="reg_verify_code")
        actions = st.columns(2)
        if actions[0].button(
            "Doğrula ve kaydol",
            key="reg_verify_btn",
            use_container_width=True,
            type="primary",
        ):
            if (code or "").strip() != pending["code"]:
                st.session_state.auth_error = "Doğrulama kodu hatalı."
                st.rerun()
            try:
                user = register_user(
                    first_name=pending["first_name"],
                    last_name=pending["last_name"],
                    email=pending["email"],
                    password=pending["password"],
                )
            except ValueError as exc:
                st.session_state.auth_error = str(exc)
                st.rerun()
            st.session_state.user = user
            st.session_state.pending_registration = None
            st.session_state.auth_open = False
            st.session_state.auth_error = ""
            st.rerun()
        if actions[1].button("Geri", key="reg_verify_back", use_container_width=True):
            st.session_state.pending_registration = None
            st.session_state.auth_error = ""
            st.rerun()
        return

    names = st.columns(2)
    with names[0]:
        st.text_input("Ad", key="reg_first")
    with names[1]:
        st.text_input("Soyad", key="reg_last")
    st.text_input("E-posta", key="reg_email", placeholder="ornek@posta.com")
    password = st.text_input("Şifre", key="reg_password", type="password")
    st.markdown(_password_checklist_html(password), unsafe_allow_html=True)
    st.text_input("Şifre (tekrar)", key="reg_password2", type="password")
    st.markdown(f'<div class="consent-copy">{_esc(CONSENT_TEXT)}</div>', unsafe_allow_html=True)
    st.checkbox("Onay metnini okudum ve kabul ediyorum.", key="reg_consent")
    if st.button("Kaydol", key="reg_submit", use_container_width=True, type="primary"):
        _start_email_verification()
        st.rerun()


@st.dialog("Hesap", width="large", on_dismiss=_close_auth_dialog)
def _auth_dialog() -> None:
    if st.session_state.auth_mode != "admin_login":
        login_col, register_col = st.columns(2)
        with login_col:
            if st.button(
                "Giriş",
                key="auth_tab_login",
                use_container_width=True,
                type="primary" if st.session_state.auth_mode == "login" else "secondary",
            ):
                st.session_state.auth_mode = "login"
                st.session_state.auth_error = ""
                st.rerun()
        with register_col:
            if st.button(
                "Kaydol",
                key="auth_tab_register",
                use_container_width=True,
                type="primary" if st.session_state.auth_mode == "register" else "secondary",
            ):
                st.session_state.auth_mode = "register"
                st.session_state.auth_error = ""
                st.rerun()

    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    if st.session_state.auth_mode == "admin_login":
        _render_admin_login_panel()
    elif st.session_state.auth_mode == "login":
        _render_login_panel()
    else:
        _render_register_panel()


def _is_admin() -> bool:
    user = st.session_state.get("user") or {}
    return user.get("role") == "admin"


def _customer_email() -> str:
    user = st.session_state.get("user") or {}
    if user.get("role") == "admin":
        return ""
    return str(user.get("email") or "").strip().lower()


def _logout() -> None:
    st.session_state.user = None
    st.session_state.chat_drawer_open = False
    st.session_state.auth_mode = "login"
    st.session_state.customer_view = "chat"


def _render_topbar() -> None:
    with st.container(key="app_topbar", horizontal=True, vertical_alignment="center", gap=None):
        if not _is_admin():
            drawer_open = bool(st.session_state.chat_drawer_open)
            if st.button(
                "☰",
                key="top_chat_btn",
                type="tertiary",
                help="Menüyü kapat" if drawer_open else "Menüyü aç",
            ):
                st.session_state.chat_drawer_open = not drawer_open
        user = st.session_state.get("user")
        if user:
            role_mark = "Yönetici · " if _is_admin() else ""
            label = (
                f"{role_mark}{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                or "Hesap"
            )
            with st.popover(label, icon=":material/person:"):
                st.caption(user.get("email", ""))
                if st.button(
                    "Çıkış",
                    key="logout_btn",
                    use_container_width=True,
                    on_click=_logout,
                ):
                    st.rerun()
        elif st.button("Giriş / Kaydol", key="top_auth_btn"):
            st.session_state.auth_open = True
            st.session_state.auth_mode = "login"
            st.session_state.auth_error = ""
            _refresh_captcha()


def _conversation_label(conv: dict) -> str:
    first_user = next(
        (item.get("content") for item in conv.get("messages") or [] if item.get("role") == "user"),
        None,
    )
    if first_user:
        return " ".join(str(first_user).split())[:42]
    if conv.get("id") == st.session_state.current_conv_id:
        return "Bu sohbet"
    return "Boş sohbet"


def _close_drawer() -> None:
    st.session_state.chat_drawer_open = False


def _record_type_label(ticket: dict) -> str:
    return str(ticket.get("path_label") or ticket.get("surec_label") or "ITSM talebi")


def _record_status_label(status: str) -> str:
    return {
        "accepted": "Onaylandı",
        "open": "Açık",
        "in_progress": "İşleniyor",
        "resolved": "Tamamlandı",
    }.get(status, status or "—")


def _render_customer_record_card(ticket: dict) -> None:
    status = str(ticket.get("status") or "")
    created = str(ticket.get("created_at") or "")
    st.markdown(
        f"""
        <div class="ticket-card glass">
          <div class="ticket-kicker">{_esc(_record_type_label(ticket))} · {_esc(_record_status_label(status))} · {_esc(created)}</div>
          <div class="ticket-title">{_esc(ticket.get("id", ""))}</div>
          <p><strong>Talebin</strong><br>{_esc(ticket.get("customer_ask", ""))}</p>
          <p><strong>Alanlar</strong><br>varlık: {_esc(ticket.get("asset"))} · konum: {_esc(ticket.get("location"))} · etki: {_esc(ticket.get("impact"))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_tickets_pane() -> None:
    with st.container(key="tickets_pane"):
        st.markdown(
            """
            <div class="tickets-bar">
              <span class="spark">✦</span>
              <span class="chat-bar-title">Kayıtlar</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user = st.session_state.get("user")
        if user and not _is_admin():
            if st.button("Çıkış", key="tickets_logout", on_click=_logout):
                st.rerun()
        elif not user:
            if st.button("Giriş", key="tickets_login"):
                st.session_state.auth_open = True
                st.session_state.auth_mode = "login"
                st.session_state.auth_error = ""
                _refresh_captcha()
                st.rerun()

        email = _customer_email()
        records = tickets_for_customer(
            email=email,
            extra_ids=list(st.session_state.get("my_ticket_ids") or []),
        )
        if not email and not records:
            st.markdown(
                '<p class="record-empty">Giriş yapınca kayıtların burada durur.<br>'
                "Sohbette ticket açınca da bu listeye düşer.</p>",
                unsafe_allow_html=True,
            )
            return
        if not records:
            st.markdown(
                '<p class="record-empty">Henüz kayıtlı ticketın yok.</p>',
                unsafe_allow_html=True,
            )
            return
        for ticket in records:
            _render_customer_record_card(ticket)


def _render_ticket_body(ticket: dict) -> None:
    urgency = ticket.get("urgency", "medium")
    bullets = "".join(f"<li>{_esc(item)}</li>" for item in ticket.get("summary_bullets", []))
    followup_html = ""
    followups = ticket.get("followups") or []
    if followups:
        items = "".join(
            f"<li>{_esc(item.get('text') if isinstance(item, dict) else item)}</li>"
            for item in followups
        )
        followup_html = f"<p><strong>Ek ayrıntı</strong></p><ul>{items}</ul>"
    st.markdown(
        f"""
        <div class="ticket-card glass">
          <div class="ticket-kicker">{_esc(ticket.get("path_label") or "ITSM")} · {_esc(ticket.get("status", "open"))} · {_esc(ticket.get("created_at", ""))}</div>
          <div class="ticket-title">{_esc(ticket["id"])}</div>
          <div class="ticket-meta">
            <span class="urgency-{_esc(urgency)}">öncelik: {_esc(urgency)}</span>
            &nbsp;· üslup: {_esc(ticket.get("sentiment"))}
          </div>
          <p><strong>Kullanıcı talebi</strong><br>{_esc(ticket.get("customer_ask", ""))}</p>
          <p><strong>Sınıf</strong><br>{_esc(ticket.get("talep_turu_label"))} → {_esc(ticket.get("birim_label"))} → {_esc(ticket.get("modul_label"))} → {_esc(ticket.get("surec_label"))}</p>
          <p><strong>Alanlar</strong><br>varlık: {_esc(ticket.get("asset"))} · konum: {_esc(ticket.get("location"))} · etki: {_esc(ticket.get("impact"))}</p>
          <p><strong>Neden açık</strong><br>{_esc(ticket.get("why_unresolved", ""))}</p>
          <p><strong>Yönetici özeti</strong></p>
          <ul>{bullets}</ul>
          <p><strong>Önerilen sonraki adım</strong><br>{_esc(ticket.get("recommended_next_step", ""))}</p>
          {followup_html}
          <p><strong>Kayıt notları</strong></p>
          <div class="handoff">{_esc(ticket.get("handoff_notes", ""))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    actions = st.columns(2)
    ticket_id = ticket["id"]
    if actions[0].button("İşleniyor", key=f"prog-{ticket_id}", use_container_width=True):
        update_status(ticket_id, "in_progress")
        st.rerun()
    if actions[1].button("Çözüldü", key=f"res-{ticket_id}", use_container_width=True):
        update_status(ticket_id, "resolved")
        st.rerun()


def _render_chat_drawer() -> None:
    _sync_conversation()
    head = st.columns([4, 1])
    with head[0]:
        st.markdown(
            '<div class="drawer-head"><span class="drawer-title">Menü</span></div>',
            unsafe_allow_html=True,
        )
    with head[1]:
        st.button("✕", key="drawer_close", help="Paneli kapat", on_click=_close_drawer)

    if st.button("Yeni sohbet", key="drawer_new_chat", use_container_width=True):
        st.session_state.customer_view = "chat"
        _reset_chat()
        st.rerun()

    if st.button(
        "Taleplerim",
        key="drawer_my_records",
        use_container_width=True,
        type="primary" if st.session_state.get("customer_view") == "records" else "secondary",
    ):
        _open_customer_records()
        st.rerun()

    for conv in reversed(st.session_state.conversations):
        active = conv["id"] == st.session_state.current_conv_id
        if st.button(
            _conversation_label(conv),
            key=f"conv-{conv['id']}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.customer_view = "chat"
            _bind_conversation(conv)
            st.rerun()
        last = next(
            (
                item.get("content")
                for item in reversed(conv.get("messages") or [])
                if item.get("role") == "user"
            ),
            "Henüz mesaj yok",
        )
        st.markdown(f'<div class="conv-preview">{_esc(last)}</div>', unsafe_allow_html=True)


def _open_customer_records() -> None:
    return


def _render_admin_home() -> None:
    top = st.columns([5, 1], vertical_alignment="center")
    with top[0]:
        st.markdown(
            """
            <div class="page-head">
              <h1 class="page-title">ITSM Asistanı</h1>
              <p class="page-sub">Yönetici kuyruğu</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top[1]:
        if st.button("Çıkış", key="admin_logout", use_container_width=True, on_click=_logout):
            st.rerun()
    st.markdown(
        """
        <div class="hero">
          <div class="admin-kicker">Yönetici</div>
          <p class="lede">ITSM kuyruğu — sınıflandırılmış talepler</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tickets = list(reversed(load_tickets()))
    if not tickets:
        st.info("Henüz ticket yok. Chatbot kayıtları burada görünür.")
    else:
        labels = [
            f"{t['id']} · {t.get('birim_label') or '—'} · {t.get('surec_label') or '—'} · {t.get('status', 'open')}"
            for t in tickets
        ]
        choice = st.selectbox("Kayıt", options=range(len(tickets)), format_func=lambda i: labels[i])
        _render_ticket_body(tickets[choice])
    jobs = list(reversed(load_jobs()))
    if jobs:
        st.markdown("#### Rapor JOB kuyruğu")
        for job in jobs[:8]:
            st.caption(
                f"{job.get('id')} · {job.get('status')} · {job.get('command', '')[:80]}"
            )
            if job.get("result"):
                st.text(job["result"])


def _render_home() -> None:
    st.markdown(
        """
        <div class="page-head">
          <h1 class="page-title">ITSM Asistanı</h1>
          <p class="page-sub">Kurum içi destek asistanı. Talebi doğal dille alır, sınıflandırır, geçmiş çözümlerden önerir ve gerektiğinde kayıt açar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="workspace"):
        left, right = st.columns([1.42, 0.78], gap="medium")
        with left:
            _render_customer_tab()
        with right:
            _render_tickets_pane()


def _render_customer_tab() -> None:
    pending = st.session_state.get("pending_prompt")
    with st.container(key="chat_shell"):
        st.markdown(
            _messages_html(
                st.session_state.messages,
                typing=bool(pending),
                picker_html="",
            ),
            unsafe_allow_html=True,
        )
        with st.form("composer", clear_on_submit=True):
            cols = st.columns([12, 1], gap="small")
            with cols[0]:
                prompt = st.text_input(
                    "mesaj",
                    placeholder="Mesaj…",
                    label_visibility="collapsed",
                )
            with cols[1]:
                sent = st.form_submit_button("➤", help="Gönder")

    if sent:
        prompt = (prompt or "").strip()
        if prompt and not pending:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.pending_prompt = prompt
            _sync_conversation()
            st.rerun()

    if pending:
        st.session_state.pending_prompt = None
        _apply_turn(pending)
        st.rerun()


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _init_state()
    if st.query_params.get("reset") == "1":
        _reset_chat()
        st.query_params.clear()
        st.rerun()

    if st.session_state.auth_open:
        _auth_dialog()

    if _is_admin():
        _render_admin_home()
        return

    _render_home()


if __name__ == "__main__":
    main()
