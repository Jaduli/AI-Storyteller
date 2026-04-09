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
    summary = data.get('summary', 'None.')
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
    result, error = utils.call_ai_api(api_url, headers, payload)

    if error:
        message, status = error
        return jsonify({"error": message}), status

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
    
    mode = data.get('mode', 'cloud')  # Default to cloud summarization
    
    summary = data.get('summary', 'None.')

    model = 'llama-3.1-8b-instant'
    
    trimmed_content = utils.trim_content_to_length(content)
    new_summary = ""

    if mode == 'cloud':
        # Validate environment configuration
        api_url = os.getenv("API_URL")
        api_key = os.getenv("API_KEY")
        
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {
                    "role": "user",
                    "content": f"STORY SUMMARY: {summary}\n\nRECENT STORY: {content}"
                }
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_summary = result["choices"][0]["message"]["content"]

    else:    
        response = requests.post(OLLAMA_URL, json={
            "model": "tinyllama",
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": f"STORY SUMMARY: {summary}\n\nRECENT STORY: {content}"}
            ],
            "options": {
                "num_predict": 200,
                "temperature": 0.7
            },
            "stream": False
        })

        if response.status_code == 200:
            new_summary = response.json().get("message", {}).get("content", "").strip()
        else:
            return {"error": response.text}, response.status_code

    trimmed = utils.trim_incomplete_sentences(new_summary)

    return jsonify({"summary": trimmed})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)