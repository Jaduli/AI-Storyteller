from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import re
from dotenv import load_dotenv
import os
from default_prompts import GENERATION_SYS_PROMPT, SUMMARIZATION_SYS_PROMPT
import utils

# Local Ollama model API endpoint
OLLAMA_URL = "http://ai:11434/api/chat"

load_dotenv()

app = Flask(__name__)
CORS(app)

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.route('/api/load', methods=['GET'])
def load_file():
    filename = request.args.get('filename')
    path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(path):
        return jsonify({"content": ""})

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    return jsonify({"content": content})


@app.route('/api/save', methods=['POST'])
def save_file():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')

    path = os.path.join(BASE_DIR, filename)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    return jsonify({"message": "File saved successfully"})

@app.route('/api/continue', methods=['POST'])
def continue_story():
    # Validate request JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    summary = data.get('summary', '')
    model = 'llama-3.1-8b-instant'

    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400
    
    # Trim content to save context length
    trimmed_content = utils.trim_content_to_length(content)

    # Validate environment configuration
    api_url = os.getenv("API_URL")
    api_key = os.getenv("API_KEY")
    if not api_url or not api_key:
        return jsonify({"error": "API_URL or API_KEY not set."}), 500

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": GENERATION_SYS_PROMPT},
            {
                "role": "user",
                "content": f"STORY SUMMARY: {summary}\n\nRECENT STORY: {content}"
            }
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }

    # Call external AI API with error handling
    response = requests.post(api_url, headers=headers, json=payload)

    try:
        result = response.json()
    except Exception:
        return jsonify({
            "error": "Invalid response from AI API.",
            "raw": response.text
        }), 500

    continued_content = result["choices"][0]["message"]["content"]

    trimmed = utils.trim_incomplete_sentences(continued_content)

    return jsonify({"continued_content": trimmed})

@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400
    
    trimmed_content = utils.trim_content_to_length(content)
    
    response = requests.post(OLLAMA_URL, json={
        "model": "tinyllama",
        "messages": [
            {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
            {"role": "user", "content": trimmed_content}
        ],
        "options": {
            "num_predict": 200,
            "temperature": 0.7
        },
        "stream": False
    })

    summary = response.json().get("message", {}).get("content", "").strip()

    trimmed = utils.trim_incomplete_sentences(summary)

    if response.status_code == 200:
        return {
            "summary": trimmed
        }
    else:
        return {"error": response.text}, response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)