"""
Reportly — Streamlit UI
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
from nlu_engine import model_available
from orchestrator import handle_turn
from tickets import load_tickets, update_status

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
    page_title="Reportly",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

WELCOME = (
    "I am the first-line complaint assistant. I will try a standard procedure first. "
    "If that cannot close it — or you ask to file a complaint — I open a specialist record "
    "with a manager brief.\n\n"
    "Try something like: *My student loan servicer never applied my payments correctly "
    "and now they say I am late even though I paid on time.*"
)

SAMPLE_COMPLAINTS = (
    {
        "name": "Maya Chen",
        "brand": "Navient",
        "text": "My student loan servicer never applied my payments correctly and now they say I am late even though I paid on time.",
    },
    {
        "name": "Jordan Hale",
        "brand": "Chase",
        "text": "The bank deducted an unexpected fee from my checking account.",
    },
    {
        "name": "Priya Shah",
        "brand": "Capital One",
        "text": "This charge is unauthorized fraud, I did not make this purchase on my credit card.",
    },
    {
        "name": "Sam Ortiz",
        "brand": "Portfolio Recovery",
        "text": "I am furious about harassing collection calls every night. This is ridiculous. File a complaint.",
    },
    {
        "name": "Elena Rossi",
        "brand": "Encore Capital",
        "text": "This is not my debt. I never owed this collector anything.",
    },
    {
        "name": "Chris Park",
        "brand": "Equifax",
        "text": "There is an incorrect account on my credit report that is not mine.",
    },
    {
        "name": "Amina Diallo",
        "brand": "Western Union",
        "text": "I sent a transfer two days ago and it still has not arrived.",
    },
    {
        "name": "Ben Walsh",
        "brand": "Ally Financial",
        "text": "I bought the car from the dealer and the transmission failed. The vehicle loan company will not help.",
    },
)

CONSENT_TEXT = (
    "By creating a Reportly account I agree that my first name, last name, and email "
    "address may be processed to open the account, verify my session, and follow my "
    "complaint record. I may withdraw this consent at any time."
)

CUSTOM_CSS = """
<style>
""" + _brand_font_face() + """
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@1,700&family=Figtree:wght@400;500;600;650&display=swap');

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
  --card-near: 88%;
  --card-spread: 124%;
  --card-off: 175%;
}

html, body, [class*="css"] {
  font-family: "Figtree", sans-serif;
  color: var(--ink);
}

html, body {
  overflow-x: hidden !important;
  overflow-y: auto !important;
  max-width: 100%;
  width: 100%;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
section.main {
  background: transparent !important;
}

.stApp,
[data-testid="stAppViewContainer"] {
  overflow-x: hidden !important;
  overflow-y: auto !important;
  width: 100% !important;
  max-width: 100% !important;
}

[data-testid="stMain"],
section.main,
.main,
.block-container {
  overflow: visible !important;
}

[data-testid="stMain"],
section.main,
.main {
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

header[data-testid="stHeader"] {
  display: none !important;
}
[data-testid="stToolbar"] { display: none; }
#MainMenu, footer { visibility: hidden; }

.block-container {
  position: relative;
  z-index: 1;
  padding-top: 4.7rem;
  padding-bottom: 2.2rem;
  padding-left: clamp(0.8rem, 4vw, 2rem);
  padding-right: clamp(0.8rem, 4vw, 2rem);
  max-width: min(920px, 100%);
}

.st-key-app_topbar {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  height: 3.4rem !important;
  min-height: 3.4rem !important;
  z-index: 1000 !important;
  margin: 0 !important;
  padding: 0 1.1rem !important;
  box-sizing: border-box !important;
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
  background: linear-gradient(
    180deg,
    rgba(77, 90, 46, 0.72) 0%,
    rgba(61, 70, 32, 0.58) 100%
  );
  backdrop-filter: blur(18px) saturate(1.3);
  -webkit-backdrop-filter: blur(18px) saturate(1.3);
  border-bottom: 1px solid rgba(246, 239, 224, 0.28);
  box-shadow: 0 10px 28px rgba(31, 36, 18, 0.18);
}
.stElementContainer:has(> .st-key-app_topbar),
[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-app_topbar) {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  border: 0 !important;
}
.st-key-app_topbar [data-testid="stVerticalBlock"],
.st-key-app_topbar [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: space-between !important;
  width: 100% !important;
  height: 3.4rem !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}
.st-key-app_topbar [data-testid="stElementContainer"],
.st-key-app_topbar .stElementContainer,
.st-key-app_topbar [data-testid="stButton"],
.st-key-app_topbar .stButton,
.st-key-app_topbar [data-testid="stPopover"] {
  margin: 0 !important;
  padding: 0 !important;
  height: 2.45rem !important;
  min-height: 2.45rem !important;
  display: flex !important;
  align-items: center !important;
}
.st-key-app_topbar [data-testid="stWidgetLabel"] {
  display: none !important;
}
.st-key-app_topbar [data-testid="stVerticalBlock"] > div:last-child,
.st-key-app_topbar [data-testid="stHorizontalBlock"] > div:last-child {
  margin-left: auto !important;
}
.st-key-app_topbar button {
  margin: 0 !important;
}
.st-key-app_topbar .st-key-top_auth_btn button,
.st-key-app_topbar [data-testid="stPopover"] > button,
.st-key-app_topbar [data-testid="stPopover"] button {
  background: var(--paper) !important;
  background-image: none !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(246, 239, 224, 0.55) !important;
  border-radius: 12px !important;
  font-weight: 650 !important;
  box-shadow: 0 2px 10px rgba(77, 90, 46, 0.16) !important;
  white-space: nowrap !important;
  height: 2.45rem !important;
  min-height: 2.45rem !important;
  max-height: 2.45rem !important;
  padding: 0 0.95rem !important;
  line-height: 2.45rem !important;
}
.st-key-app_topbar .st-key-top_auth_btn button:hover,
.st-key-app_topbar [data-testid="stPopover"] button:hover {
  background: linear-gradient(135deg, #FC9C51, #E9767F) !important;
  color: var(--paper) !important;
  border-color: transparent !important;
}
.st-key-app_topbar .st-key-top_chat_btn button {
  width: 2.45rem !important;
  height: 2.45rem !important;
  min-height: 2.45rem !important;
  max-height: 2.45rem !important;
  padding: 0 !important;
  border-radius: 12px !important;
  font-size: 1.15rem !important;
  line-height: 2.45rem !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: transparent !important;
  background-image: none !important;
  color: var(--paper) !important;
  border: 1.5px solid rgba(246, 239, 224, 0.55) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 0 0 1px rgba(31, 36, 18, 0.16) !important;
}
.st-key-app_topbar .st-key-top_chat_btn button:hover {
  background: rgba(246, 239, 224, 0.1) !important;
  color: var(--paper) !important;
}

.st-key-chat_drawer {
  position: fixed !important;
  top: 3.4rem !important;
  left: 0 !important;
  width: min(300px, 86vw) !important;
  height: calc(100vh - 3.4rem) !important;
  max-height: calc(100vh - 3.4rem) !important;
  z-index: 996 !important;
  margin: 0 !important;
  padding: 0.85rem 0.8rem 1.15rem !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
  box-sizing: border-box !important;
  pointer-events: auto !important;
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.92) 0%,
    rgba(77, 90, 46, 0.88) 55%,
    rgba(61, 70, 32, 0.92) 100%
  );
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  border: 1px solid rgba(246, 239, 224, 0.28);
  border-left: 0;
  border-bottom: 0;
  border-radius: 0 18px 0 0;
  box-shadow: 12px 0 36px rgba(31, 36, 18, 0.22);
  animation: drawer-in 0.28s ease;
}
@keyframes drawer-in {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}
.st-key-chat_drawer button,
.st-key-chat_drawer [data-testid^="stBaseButton"] {
  pointer-events: auto !important;
  position: relative !important;
  z-index: 2 !important;
}
.st-key-chat_drawer div.stButton > button {
  background: var(--paper) !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(246, 239, 224, 0.45) !important;
  box-shadow: 0 2px 10px rgba(31, 36, 18, 0.12) !important;
}
.st-key-chat_drawer div.stButton > button:hover {
  background: linear-gradient(135deg, #FC9C51, #E9767F) !important;
  color: var(--paper) !important;
}
.st-key-chat_drawer .st-key-drawer_close div.stButton > button {
  width: 2.2rem !important;
  min-height: 2.2rem !important;
  border-radius: 10px !important;
  padding: 0 !important;
}
.drawer-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.65rem;
}
.drawer-title {
  font-family: "Bodoni Moda", serif;
  font-style: italic;
  font-size: 1.15rem;
  color: var(--paper);
}
.conv-preview {
  font-size: 0.78rem;
  color: var(--muted);
  margin: -0.15rem 0 0.55rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

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
  background-color: transparent !important;
  background-image: none !important;
  color: rgba(77, 90, 46, 0.4) !important;
  border: 0 !important;
  box-shadow: none !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  min-height: 1.6rem !important;
  height: auto !important;
  padding: 0.15rem 0 !important;
  letter-spacing: 0.02em !important;
}
.st-key-admin_entry_btn button:hover,
[data-testid="stDialog"] .st-key-admin_entry_btn button:hover,
div[role="dialog"] .st-key-admin_entry_btn button:hover {
  background: none !important;
  background-image: none !important;
  color: rgba(77, 90, 46, 0.72) !important;
  border: 0 !important;
  box-shadow: none !important;
}
.st-key-admin_back_btn button {
  background: none !important;
  background-image: none !important;
  color: var(--olive) !important;
  border: 0 !important;
  box-shadow: none !important;
  font-size: 0.82rem !important;
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

.brand {
  font-family: "Calfine", serif !important;
  font-style: normal !important;
  font-weight: 400 !important;
  font-synthesis: none;
  font-size: clamp(2.2rem, 11vw, 5.4rem) !important;
  line-height: 1.08;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  transform: scaleX(1.18);
  transform-origin: center center;
  color: var(--paper);
  margin: 0 auto 0.7rem auto;
  width: max-content;
  max-width: 100%;
}

.lede,
p.lede {
  font-size: clamp(0.88rem, 0.75rem + 1.1vw, 1.02rem);
  line-height: 1.55;
  color: var(--paper);
  max-width: 44rem;
  margin: 0 auto 0.4rem auto !important;
  text-align: center !important;
  padding: 0 0.2rem;
  width: 100%;
}

.glass {
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.62) 0%,
    rgba(77, 90, 46, 0.52) 55%,
    rgba(61, 70, 32, 0.58) 100%
  );
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  border: 1px solid rgba(246, 239, 224, 0.28);
  box-shadow:
    0 18px 50px rgba(77, 90, 46, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}

.chat-panel {
  position: relative;
  margin-top: 0.35rem;
  border-radius: 22px 22px 0 0;
  overflow: hidden;
  color: var(--cream);
  font-size: clamp(0.78rem, 0.55rem + 1.1vw, 1rem);
}

.chat-bar {
  display: flex;
  align-items: center;
  gap: 0.65em;
  padding: 0.85em 1.1em;
  border-bottom: 1px solid rgba(246, 239, 224, 0.16);
  background: linear-gradient(90deg, rgba(196, 186, 101, 0.18), rgba(254, 198, 124, 0.1));
  min-width: 0;
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
.new-chat,
.new-chat:link,
.new-chat:visited,
.new-chat:hover,
.new-chat:active {
  margin-left: auto;
  color: #4D5A2E !important;
  background: var(--paper);
  text-decoration: none !important;
  text-transform: lowercase;
  border-bottom: none !important;
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
  height: clamp(220px, 48vh, 440px);
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
  max-width: min(82%, 560px);
  padding: 0.78em 0.95em 0.7em;
  border-radius: 16px;
  line-height: 1.5;
  font-size: 0.96em;
  word-wrap: break-word;
  overflow-wrap: anywhere;
}
.bubble.assistant {
  background: rgba(246, 239, 224, 0.14);
  border: 1px solid rgba(246, 239, 224, 0.28);
  border-bottom-left-radius: 6px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16);
}
.bubble.user {
  background: linear-gradient(135deg, #FC9C51 0%, #E9767F 58%, #A16A84 140%);
  color: var(--paper);
  border-bottom-right-radius: 6px;
  box-shadow: 0 8px 20px rgba(233, 118, 127, 0.28);
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
  font-size: 1.45rem;
  margin: 0.2rem 0 0.7rem 0;
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

[data-testid="stForm"] {
  border: 1px solid rgba(246, 239, 224, 0.28) !important;
  border-top: 1px solid rgba(246, 239, 224, 0.12) !important;
  border-radius: 0 0 22px 22px !important;
  background: linear-gradient(
    180deg,
    rgba(77, 90, 46, 0.5),
    rgba(61, 70, 32, 0.58)
  ) !important;
  backdrop-filter: blur(22px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(22px) saturate(1.3) !important;
  padding: 0.85rem 0.9rem 0.95rem !important;
  box-shadow: 0 18px 50px rgba(77, 90, 46, 0.18);
  max-width: 100% !important;
  box-sizing: border-box !important;
}

[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  gap: 0.35rem !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] > div,
[data-testid="stForm"] [data-testid="column"],
[data-testid="stForm"] [data-testid="stColumn"] {
  min-width: 0 !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] > div:first-child,
[data-testid="stForm"] [data-testid="column"]:first-child,
[data-testid="stForm"] [data-testid="stColumn"]:first-child {
  flex: 1 1 auto !important;
  width: auto !important;
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] > div:last-child,
[data-testid="stForm"] [data-testid="column"]:last-child,
[data-testid="stForm"] [data-testid="stColumn"]:last-child {
  flex: 0 0 2.6rem !important;
  width: 2.6rem !important;
  min-width: 2.6rem !important;
  max-width: 2.6rem !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] {
  width: 100% !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] input,
[data-testid="stForm"] [data-testid="stTextInput"] > div > div {
  background: var(--paper) !important;
  color: #4D5A2E !important;
  border: 1px solid rgba(77, 90, 46, 0.18) !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(77, 90, 46, 0.12) !important;
  min-height: 2.55rem !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
  color: #5E5C2D !important;
  opacity: 0.72 !important;
}
[data-testid="stForm"] [data-testid="stTextInput"] input:focus {
  border-color: #4D5A2E !important;
  box-shadow: 0 0 0 3px rgba(77, 90, 46, 0.18) !important;
}

[data-testid="stForm"] div.stButton > button,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stForm"] button[kind="secondaryFormSubmit"],
[data-testid="stForm"] button[kind="formSubmit"] {
  background: none !important;
  background-color: transparent !important;
  background-image: none !important;
  color: var(--paper) !important;
  font-size: 1.7rem !important;
  font-weight: 800 !important;
  line-height: 1 !important;
  min-height: 2.55rem !important;
  height: 2.55rem !important;
  width: 2.55rem !important;
  max-width: 2.55rem !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  backdrop-filter: none !important;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] {
  background: none !important;
  border: 0 !important;
  box-shadow: none !important;
}
[data-testid="stForm"] div.stButton > button p,
[data-testid="stForm"] div.stButton > button div,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] p,
[data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"] p {
  font-size: 1.7rem !important;
  color: var(--paper) !important;
  background: none !important;
}
[data-testid="stForm"] div.stButton > button:hover,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover,
[data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
  background: none !important;
  background-color: transparent !important;
  color: #F3EBE0 !important;
  box-shadow: none !important;
  border: 0 !important;
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

.sample-ticker {
  position: relative;
  z-index: 2;
  margin: 1rem 0 0.5rem;
  overflow-x: clip;
  overflow-y: visible;
  background: none;
  border: 0;
  box-shadow: none;
  padding: 0.2rem 0 1.1rem;
  max-width: 100%;
}
.sample-ticker-stage {
  position: relative;
  height: clamp(11.6rem, 42vw, 13rem);
  overflow: visible;
  isolation: isolate;
}
.sample-card {
  position: absolute;
  top: auto;
  bottom: 0.15rem;
  left: 50%;
  width: min(280px, 48%);
  box-sizing: border-box;
  padding: 0.78em 0.9em 0.85em;
  border-radius: 14px;
  background: linear-gradient(
    165deg,
    rgba(94, 92, 45, 0.62) 0%,
    rgba(77, 90, 46, 0.52) 55%,
    rgba(61, 70, 32, 0.58) 100%
  );
  backdrop-filter: blur(22px) saturate(1.35);
  -webkit-backdrop-filter: blur(22px) saturate(1.35);
  border: 1px solid rgba(246, 239, 224, 0.28);
  color: var(--cream);
  font-size: clamp(0.72rem, 0.58rem + 1.15vw, 0.92rem);
  transform-origin: center bottom;
  animation-name: sample-ltr;
  animation-timing-function: cubic-bezier(0.45, 0.05, 0.55, 0.95);
  animation-iteration-count: infinite;
  animation-fill-mode: both;
  will-change: transform, filter, opacity, box-shadow;
  pointer-events: none;
}
.sample-card-kicker {
  font-size: 0.68em;
  font-weight: 650;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.sample-card-name {
  margin-top: 0.08em;
  font-size: 1em;
  font-weight: 650;
  line-height: 1.2;
  color: var(--paper);
}
.sample-card-brand {
  margin-top: 0.28em;
  font-size: 0.92em;
  font-weight: 600;
  color: var(--apricot);
}
.sample-card-text {
  margin-top: 0.28em;
  font-size: 0.85em;
  line-height: 1.4;
  color: var(--cream);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
@media (max-width: 720px) {
  :root {
    --card-near: 78%;
    --card-spread: 104%;
    --card-off: 155%;
  }
  .brand {
    transform: none;
    letter-spacing: 0.01em;
  }
  .chat-bar-sub { display: none; }
  .chat-panel { border-radius: 16px 16px 0 0; }
  [data-testid="stForm"] { border-radius: 0 0 16px 16px !important; padding: 0.65rem 0.65rem 0.7rem !important; }
  .sample-card { width: min(230px, 62%); }
}
@media (max-width: 480px) {
  :root {
    --card-near: 74%;
    --card-spread: 98%;
  }
  .chat-thread { height: clamp(200px, 44vh, 280px); }
}
@media (prefers-reduced-motion: reduce) {
  .sample-card { animation: none !important; opacity: 0; filter: none; transform: translateX(-50%); }
  .sample-card:first-of-type { opacity: 1; }
  .bubble.typing span { animation: none; opacity: 0.7; }
}
</style>
"""


def _blank_conversation() -> dict:
    return {
        "id": uuid.uuid4().hex[:10],
        "title": "New chat",
        "messages": [{"role": "assistant", "content": WELCOME}],
        "phase": "open",
        "last_rule_id": None,
        "last_ticket_id": None,
        "last_debug": None,
        "pending_prompt": None,
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


def _sync_conversation() -> None:
    conv = _current_conversation()
    conv["messages"] = st.session_state.messages
    conv["phase"] = st.session_state.phase
    conv["last_rule_id"] = st.session_state.last_rule_id
    conv["last_ticket_id"] = st.session_state.last_ticket_id
    conv["last_debug"] = st.session_state.last_debug
    conv["pending_prompt"] = st.session_state.get("pending_prompt")
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
    st.session_state.setdefault("captcha_field_key", 0)
    st.session_state.setdefault("auth_open", False)
    st.session_state.setdefault("auth_mode", "login")
    st.session_state.setdefault("auth_error", "")
    st.session_state.setdefault("pending_registration", None)
    st.session_state.setdefault("chat_drawer_open", False)
    st.session_state.setdefault("user", None)
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
    rule = debug.get("rule_id") or "—"
    action = debug.get("action") or "—"
    conf = debug.get("confidence") or 0
    return (
        f"topic: {debug.get('category', '—')} ({conf:.0%}) · "
        f"sentiment: {debug.get('sentiment', '—')} · "
        f"rule: {rule} · action: {action}"
    )


def _esc(value: object) -> str:
    return html.escape(str(value or ""))


def _sample_ticker_html() -> str:
    n = max(len(SAMPLE_COMPLAINTS), 1)
    hold = 2.0
    move = 1.9
    slot = hold + move
    cycle = n * slot
    h = (hold / cycle) * 100
    p = h + (move / cycle) * 100

    center = (
        "transform:translateX(-50%) scale(1.07);filter:blur(0);opacity:1;z-index:5;"
        "box-shadow:0 22px 44px rgba(31,36,18,.48),0 8px 18px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.3)"
    )
    left_near = (
        "transform:translateX(-50%) translateX(calc(-1 * var(--card-near))) scale(0.88);"
        "filter:blur(2px);opacity:0.9;z-index:4;"
        "box-shadow:0 6px 14px rgba(31,36,18,.16)"
    )
    right_near = (
        "transform:translateX(-50%) translateX(var(--card-near)) scale(0.88);"
        "filter:blur(2px);opacity:0.9;z-index:4;"
        "box-shadow:0 6px 14px rgba(31,36,18,.16)"
    )
    off_left = (
        "transform:translateX(-50%) translateX(calc(-1 * var(--card-off))) scale(0.84);"
        "filter:blur(4px);opacity:0;z-index:1;box-shadow:none"
    )
    off_right = (
        "transform:translateX(-50%) translateX(var(--card-off)) scale(0.84);"
        "filter:blur(4px);opacity:0;z-index:1;box-shadow:none"
    )

    def card(index: int, item: dict) -> str:
        delay = -((n - index) % n) * slot
        return (
            f'<article class="sample-card" style="animation-duration:{cycle:.2f}s;'
            f'animation-delay:{delay:.2f}s">'
            '<div class="sample-card-kicker">name</div>'
            f'<div class="sample-card-name">{_esc(item["name"])}</div>'
            '<div class="sample-card-kicker" style="margin-top:0.28rem">brand</div>'
            f'<div class="sample-card-brand">{_esc(item["brand"])}</div>'
            '<div class="sample-card-kicker" style="margin-top:0.28rem">complaint</div>'
            f'<div class="sample-card-text">{_esc(item["text"])}</div>'
            "</article>"
        )

    cards = "".join(card(index, item) for index, item in enumerate(SAMPLE_COMPLAINTS))
    return (
        "<style>"
        "@keyframes sample-ltr {"
        f"0%{{{center}}}"
        f"{h:.3f}%{{{center}}}"
        f"{p:.3f}%{{{right_near}}}"
        f"{p + h:.3f}%{{{right_near}}}"
        f"{2 * p:.3f}%{{{off_right}}}"
        f"{100 - 2 * p:.3f}%{{{off_left}}}"
        f"{100 - 2 * p + h:.3f}%{{{off_left}}}"
        f"{100 - p:.3f}%{{{left_near}}}"
        f"{100 - p + h:.3f}%{{{left_near}}}"
        f"100%{{{center}}}"
        "}"
        "</style>"
        '<div class="sample-ticker">'
        f'<div class="sample-ticker-stage">{cards}</div>'
        "</div>"
    )


def _format_text(text: str) -> str:
    escaped = html.escape(text or "")
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped.replace("\n", "<br>")


def _messages_html(messages: list[dict], typing: bool = False) -> str:
    parts = [
        """
        <div class="chat-panel glass">
          <div class="chat-bar">
            <span class="spark">✦</span>
            <span class="chat-bar-title">Assistant</span>
            <span class="chat-bar-sub">first line · rule first</span>
            <a class="new-chat" href="?reset=1">new chat</a>
          </div>
          <div class="chat-thread">
        """
    ]
    for message in messages:
        role = message.get("role", "assistant")
        css_role = "user" if role == "user" else "assistant"
        body = _format_text(str(message.get("content", "")))
        meta = ""
        if css_role == "assistant" and message.get("debug"):
            meta = f'<div class="bubble-meta">{html.escape(_debug_line(message["debug"]))}</div>'
        parts.append(
            f'<div class="bubble-row {css_role}">'
            f'<div class="bubble {css_role}">{body}{meta}</div>'
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
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": result.reply, "debug": result.debug}
    )
    st.session_state.phase = result.phase
    st.session_state.last_rule_id = result.last_rule_id
    st.session_state.last_debug = result.debug
    if result.ticket:
        st.session_state.last_ticket_id = result.ticket["id"]
    _sync_conversation()


def _password_checklist_html(password: str) -> str:
    checks = password_checks(password)
    labels = (
        ("length", "At least 12 characters"),
        ("upper", "At least one uppercase letter"),
        ("lower", "At least one lowercase letter"),
        ("digit", "At least one number"),
        ("special", "At least one special character"),
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
    email = st.text_input("Email", key="login_email", placeholder="you@example.com")
    password = st.text_input("Password", key="login_password", type="password")
    st.caption("Captcha check")
    cap_row = st.columns([3, 1])
    with cap_row[0]:
        letters = "".join(f"<span>{_esc(ch)}</span>" for ch in st.session_state.captcha_answer)
        st.markdown(f'<div class="captcha-box">{letters}</div>', unsafe_allow_html=True)
    with cap_row[1]:
        if st.button("Refresh", key="captcha_refresh", use_container_width=True):
            _refresh_captcha()
            st.rerun()
    captcha = st.text_input(
        "Enter the code from the image",
        key=f"login_captcha_{st.session_state.captcha_field_key}",
    )
    if st.button("Log in", key="login_submit", use_container_width=True, type="primary"):
        if not captcha_matches(st.session_state.captcha_answer, captcha):
            st.session_state.auth_error = "Captcha check failed."
            _refresh_captcha()
            st.rerun()
        user = authenticate(email, password, role="customer")
        if not user:
            st.session_state.auth_error = "Email or password is incorrect."
            _refresh_captcha()
            st.rerun()
        st.session_state.user = user
        st.session_state.auth_open = False
        st.session_state.auth_error = ""
        st.rerun()
    st.button(
        "Admin login",
        key="admin_entry_btn",
        type="tertiary",
        on_click=lambda: st.session_state.update(auth_mode="admin_login", auth_error=""),
    )


def _render_admin_login_panel() -> None:
    st.caption("Administrator")
    email = st.text_input("Email", key="admin_email")
    password = st.text_input("Password", key="admin_password", type="password")
    if st.button("Log in", key="admin_submit", use_container_width=True, type="primary"):
        user = authenticate(email, password, role="admin")
        if not user:
            st.session_state.auth_error = "Admin login failed."
            st.rerun()
        st.session_state.user = user
        st.session_state.auth_open = False
        st.session_state.auth_error = ""
        st.session_state.chat_drawer_open = False
        st.rerun()
    st.button(
        "Back to customer login",
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
        st.session_state.auth_error = "First and last name are required."
        return
    if not is_valid_email(email):
        st.session_state.auth_error = "Enter a valid email address."
        return
    if find_user(email):
        st.session_state.auth_error = "An account with this email already exists."
        return
    issues = password_issues(password)
    if issues:
        st.session_state.auth_error = " ".join(issues)
        return
    if password != confirm:
        st.session_state.auth_error = "Passwords do not match."
        return
    if not consent:
        st.session_state.auth_error = "Please accept the consent notice to continue."
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
            f"A verification code was sent to {pending['email']}. "
            f"Demo code: **{pending['code']}**"
        )
        code = st.text_input("Email verification code", key="reg_verify_code")
        actions = st.columns(2)
        if actions[0].button(
            "Verify and sign up",
            key="reg_verify_btn",
            use_container_width=True,
            type="primary",
        ):
            if (code or "").strip() != pending["code"]:
                st.session_state.auth_error = "Verification code is incorrect."
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
        if actions[1].button("Back", key="reg_verify_back", use_container_width=True):
            st.session_state.pending_registration = None
            st.session_state.auth_error = ""
            st.rerun()
        return

    names = st.columns(2)
    with names[0]:
        st.text_input("First name", key="reg_first")
    with names[1]:
        st.text_input("Last name", key="reg_last")
    st.text_input("Email", key="reg_email", placeholder="you@example.com")
    password = st.text_input("Password", key="reg_password", type="password")
    st.markdown(_password_checklist_html(password), unsafe_allow_html=True)
    st.text_input("Password (again)", key="reg_password2", type="password")
    st.markdown(f'<div class="consent-copy">{_esc(CONSENT_TEXT)}</div>', unsafe_allow_html=True)
    st.checkbox("I have read and accept the consent notice.", key="reg_consent")
    if st.button("Sign up", key="reg_submit", use_container_width=True, type="primary"):
        _start_email_verification()
        st.rerun()


@st.dialog("Account", width="large", on_dismiss=_close_auth_dialog)
def _auth_dialog() -> None:
    if st.session_state.auth_mode != "admin_login":
        login_col, register_col = st.columns(2)
        with login_col:
            if st.button(
                "Log in",
                key="auth_tab_login",
                use_container_width=True,
                type="primary" if st.session_state.auth_mode == "login" else "secondary",
            ):
                st.session_state.auth_mode = "login"
                st.session_state.auth_error = ""
                st.rerun()
        with register_col:
            if st.button(
                "Sign up",
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


def _logout() -> None:
    st.session_state.user = None
    st.session_state.chat_drawer_open = False
    st.session_state.auth_mode = "login"


def _render_topbar() -> None:
    with st.container(key="app_topbar", horizontal=True, vertical_alignment="center", gap=None):
        if not _is_admin():
            drawer_open = bool(st.session_state.chat_drawer_open)
            if st.button(
                "☰",
                key="top_chat_btn",
                type="tertiary",
                help="Close menu" if drawer_open else "Open menu",
            ):
                st.session_state.chat_drawer_open = not drawer_open
        user = st.session_state.get("user")
        if user:
            role_mark = "Admin · " if _is_admin() else ""
            label = (
                f"{role_mark}{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                or "Account"
            )
            with st.popover(label, icon=":material/person:"):
                st.caption(user.get("email", ""))
                if st.button(
                    "Log out",
                    key="logout_btn",
                    use_container_width=True,
                    on_click=_logout,
                ):
                    st.rerun()
        elif st.button("Log in / Sign up", key="top_auth_btn"):
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
        return "Current chat"
    return "Empty chat"


def _close_drawer() -> None:
    st.session_state.chat_drawer_open = False


def _render_ticket_body(ticket: dict) -> None:
    urgency = ticket.get("urgency", "medium")
    bullets = "".join(f"<li>{_esc(item)}</li>" for item in ticket.get("summary_bullets", []))
    rules = ", ".join(ticket.get("tried_rules") or ["—"])
    followup_html = ""
    followups = ticket.get("followups") or []
    if followups:
        items = "".join(
            f"<li>{_esc(item.get('text') if isinstance(item, dict) else item)}</li>"
            for item in followups
        )
        followup_html = f"<p><strong>Extra detail</strong></p><ul>{items}</ul>"
    st.markdown(
        f"""
        <div class="ticket-card glass">
          <div class="ticket-kicker">{_esc(ticket.get("status", "open"))} · {_esc(ticket.get("created_at", ""))}</div>
          <div class="ticket-title">{_esc(ticket["id"])}</div>
          <div class="ticket-meta">
            <span class="urgency-{_esc(urgency)}">urgency: {_esc(urgency)}</span>
            &nbsp;· category: {_esc(ticket.get("category"))}
            ({ticket.get("category_confidence", 0):.0%})
            &nbsp;· sentiment: {_esc(ticket.get("sentiment"))}
          </div>
          <p><strong>Customer ask</strong><br>{_esc(ticket.get("customer_ask", ""))}</p>
          <p><strong>Why unresolved</strong><br>{_esc(ticket.get("why_unresolved", ""))}</p>
          <p><strong>Rules tried</strong><br>{_esc(rules)}</p>
          <p><strong>Manager brief</strong></p>
          <ul>{bullets}</ul>
          <p><strong>Recommended next step</strong><br>{_esc(ticket.get("recommended_next_step", ""))}</p>
          {followup_html}
          <p><strong>Record notes</strong></p>
          <div class="handoff">{_esc(ticket.get("handoff_notes", ""))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    actions = st.columns(2)
    ticket_id = ticket["id"]
    if actions[0].button("In progress", key=f"prog-{ticket_id}", use_container_width=True):
        update_status(ticket_id, "in_progress")
        st.rerun()
    if actions[1].button("Resolved", key=f"res-{ticket_id}", use_container_width=True):
        update_status(ticket_id, "resolved")
        st.rerun()


def _render_chat_drawer() -> None:
    _sync_conversation()
    head = st.columns([4, 1])
    with head[0]:
        st.markdown(
            '<div class="drawer-head"><span class="drawer-title">Menu</span></div>',
            unsafe_allow_html=True,
        )
    with head[1]:
        st.button("✕", key="drawer_close", help="Close panel", on_click=_close_drawer)

    if st.button("New chat", key="drawer_new_chat", use_container_width=True):
        _reset_chat()
        st.rerun()

    for conv in reversed(st.session_state.conversations):
        active = conv["id"] == st.session_state.current_conv_id
        if st.button(
            _conversation_label(conv),
            key=f"conv-{conv['id']}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            _bind_conversation(conv)
            st.rerun()
        last = next(
            (
                item.get("content")
                for item in reversed(conv.get("messages") or [])
                if item.get("role") == "user"
            ),
            "No messages yet",
        )
        st.markdown(f'<div class="conv-preview">{_esc(last)}</div>', unsafe_allow_html=True)


def _render_admin_home() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="admin-kicker">Admin</div>
          <div class="brand">Reportly</div>
          <p class="lede">Complaint queue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tickets = list(reversed(load_tickets()))
    if not tickets:
        st.info("No records yet. Unresolved complaints from customer chat appear here.")
        return
    labels = [
        f"{t['id']} · {t.get('urgency', '?')} · {t.get('category', '?')} · {t.get('status', 'open')}"
        for t in tickets
    ]
    choice = st.selectbox("Record", options=range(len(tickets)), format_func=lambda i: labels[i])
    _render_ticket_body(tickets[choice])


def _render_home() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="brand">Reportly</div>
          <p class="lede">Here for your reports.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not model_available():
        st.warning(
            "No category model; rules still run. "
            "For full routing, run `python src\\classic_nlu.py` from the project root."
        )

    _render_customer_tab()
    st.markdown(_sample_ticker_html(), unsafe_allow_html=True)


def _render_customer_tab() -> None:
    pending = st.session_state.get("pending_prompt")
    st.markdown(
        _messages_html(st.session_state.messages, typing=bool(pending)),
        unsafe_allow_html=True,
    )

    with st.form("composer", clear_on_submit=True):
        cols = st.columns([12, 1], gap="small")
        with cols[0]:
            prompt = st.text_input(
                "complaint",
                placeholder="Write your complaint…",
                label_visibility="collapsed",
            )
        with cols[1]:
            sent = st.form_submit_button("➤", help="Send")

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

    _render_topbar()
    if st.session_state.auth_open:
        _auth_dialog()

    if _is_admin():
        _render_admin_home()
        return

    if st.session_state.chat_drawer_open:
        with st.container(key="chat_drawer"):
            _render_chat_drawer()

    _render_home()


if __name__ == "__main__":
    main()
