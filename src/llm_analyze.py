import json
import re
import requests

url = "http://localhost:11434/api/generate"

complaint = (
    "My student loan servicer never applied my payments correctly "
    "and now they say I am late even though I paid on time."
)

# Prompt = role + task + format + constraints
prompt = f"""
You are a customer support analyst.

Read the complaint below and respond with ONLY valid JSON.
No markdown. No extra text. No code fences.

JSON schema:
{{
  "category": "one short product category label",
  "sentiment": "negative|neutral|positive",
  "summary": "one or two sentence summary",
  "suggested_reply": "a short professional customer support reply"
}}

Complaint:
{complaint}
""".strip()

payload = {
    "model": "llama3.2",
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.2,  # more stable / less creative
    },
}

print("Asking Ollama (may be slow)...")
response = requests.post(url, json=payload, timeout=600)
response.raise_for_status()

raw = response.json().get("response", "")
print("\n--- RAW MODEL OUTPUT ---")
print(raw)
print("------------------------\n")


def extract_json(text: str):
    """Try to parse JSON even if model wraps it or forgets a closing brace."""
    text = text.strip()

    # remove ```json ... ``` if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    candidates = [text]

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.insert(0, match.group(0))

    # if it looks like JSON object started but not closed, try adding }
    if "{" in text and "}" not in text:
        candidates.append(text + "\n}")

    last_error = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            last_error = e

    raise last_error


try:
    data = extract_json(raw)
    print("Parsed JSON:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("Could not parse JSON:", e)