import os
from flask import Flask, jsonify, request, render_template
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>OK</h1>"

@app.route("/generate", methods=["POST"])
def generate():
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    return jsonify({"test": "OK"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
