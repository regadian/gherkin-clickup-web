from flask import Flask, request, jsonify, render_template
import os
import requests

app = Flask(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID")
APP_VERSION = os.getenv("APP_VERSION", "")
CUSTOM_FIELD_ID_VERSI = os.getenv("CLICKUP_CUSTOM_FIELD_VERSI", "")

def generate_gherkin(desc: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
Buat SATU test case dalam format Gherkin (Bahasa Indonesia) untuk fitur: {desc}
Gunakan struktur:
Feature: ...
  Scenario: ...
    Given ...
    When ...
    Then ...

Jangan tambahkan penjelasan, judul, atau markdown selain format Gherkin.
    """.strip()
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500
        }
    }
    
    resp = requests.post(url, json=payload)
    
    if resp.status_code != 200:
        error_msg = resp.json().get("error", {}).get("message", resp.text)
        raise Exception(f"Gemini error: {resp.status_code} – {error_msg}")
    
    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return text
    except (KeyError, IndexError):
        raise Exception("Gagal mengekstrak respons dari Gemini")

def create_clickup_task(name: str, gherkin: str) -> str:
    # Perbaiki: hapus spasi di URL (sebelumnya ada spasi di "  {CLICKUP_LIST_ID}")
    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
    
    payload = {
        "name": f"[TC] {name}",
        "description": f"```gherkin\n{gherkin}\n```",
        "status": "To Do",
        "priority": 3
    }
    
    if CUSTOM_FIELD_ID_VERSI and APP_VERSION:
        payload["custom_fields"] = [{"id": CUSTOM_FIELD_ID_VERSI, "value": APP_VERSION}]
    
    headers = {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    
    if resp.status_code not in (200, 201):
        raise Exception(f"ClickUp error: {resp.status_code} – {resp.text}")
    
    return resp.json()["url"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    feature = data.get("feature", "").strip()
    if not feature:
        return jsonify({"error": "Deskripsi fitur diperlukan"}), 400

    try:
        gherkin = generate_gherkin(feature)
        task_url = create_clickup_task(feature, gherkin)
        return jsonify({
            "gherkin": gherkin,
            "clickup_url": task_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

