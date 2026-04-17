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

BASE_DIR = "files" # Directory to store story files
os.makedirs(BASE_DIR, exist_ok=True)


# Backend Functions #

"""
/load

Load story file content, summary, and plot essentials. 
Returns 400 if filename is missing, 404 if file not found, and 500 for other errors.
"""
@app.route('/api/load', methods=['GET'])
def load_file():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            content = data.get("content", "")
            summary = data.get("summary", "None.")
            plot_essentials = data.get("plot_essentials", "None.")
    except Exception as e:
        # Internal Server Error
        return jsonify({"error": str(e)}), 500

    return jsonify({"content": content, "summary": summary, "plot_essentials": plot_essentials})

"""
/save

Save story file content, summary, and plot essentials. 
Returns 400 if filename is missing.
"""
@app.route('/api/save', methods=['POST'])
def save_file():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    summary = data.get('summary', 'None.')
    plot_essentials = data.get('plot_essentials', 'None.')

    if not filename:
        return jsonify({"error": "Filename is required"}), 400
    
    path = os.path.join(BASE_DIR, filename)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"content": content, "summary": summary, "plot_essentials": plot_essentials}, f, ensure_ascii=False, indent=2)

    return jsonify({"message": "File saved as " + filename + "."})

"""
/continue

Continue story using external AI API. 
Returns 400 for missing/invalid JSON, empty content, or missing model; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API errors, or if AI API returns empty content.
"""
@app.route('/api/continue', methods=['POST'])
def continue_story():
    # Validate request JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400

    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400

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
            {"role": "user", "content": content}
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

    if not continued_content or continued_content.strip() == "":
        return jsonify({"error": "AI API returned empty content."}), 500

    trimmed = utils.trim_incomplete_sentences(continued_content)

    return jsonify({"continued_content": trimmed})

"""
/summarize

Summarize story using external AI API (local currently not in use).
Returns 400 for missing/invalid JSON, empty content, or missing model;
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API errors, or if AI API returns empty summary.
"""
@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400
    
    mode = data.get('mode', 'cloud')  # Default to cloud summarization

    model = 'llama-3.1-8b-instant'
    
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
                {"role": "user", "content": content}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_summary = result["choices"][0]["message"]["content"]

    else:
        # Local summarization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": "tinyllama",
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
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