from flask import Flask, request, jsonify, render_template
import os
import requests

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("MY_OPENAI_KEY")
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID")


def generate_gherkin(desc):
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": f"""
Buat SATU test case Gherkin dalam Bahasa Indonesia untuk fitur: {desc}
Format: Feature, Scenario, Given, When, Then. Jangan tambahkan teks lain.
            """.strip()}],
            "temperature": 0.3
        }
    )
    if resp.status_code != 200:
        raise Exception(f"OpenAI error: {resp.status_code} – {resp.text}")
    return resp.json()["choices"][0]["message"]["content"].strip()

def create_clickup_task(name, gherkin):
    payload = {
        "name": f"[TC] {name}",
        "description": f"```gherkin\n{gherkin}\n```",
        "status": "To Do",
        "priority": 3
    }
   
    resp = requests.post(
        f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task",
        headers={"Authorization": CLICKUP_API_TOKEN},
        json=payload
    )
    if resp.status_code not in (200, 201):
        raise Exception(f"ClickUp error: {resp.status_code} – {resp.text}")
    return resp.json()["url"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    feature = data.get("feature", "").strip()
    if not feature:
        return jsonify({"error": "Deskripsi fitur diperlukan"}), 400

    try:
        gherkin = generate_gherkin(feature)
        url = create_clickup_task(feature, gherkin)
        return jsonify({"gherkin": gherkin, "clickup_url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
