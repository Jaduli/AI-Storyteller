from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import re
from dotenv import load_dotenv
import os
from default_prompts import GENERATION_SYS_PROMPT, SUMMARIZATION_SYS_PROMPT, MEMORY_SYS_PROMPT
import utils
import database

# Initialize the database
database.init_db()

# Local Ollama model API endpoint and model
OLLAMA_URL = "http://ai:11434/api/chat"
OLLAMA_MODEL = "llama3:8b"

load_dotenv()
api_url = os.getenv("API_URL")
api_key = os.getenv("API_KEY")

app = Flask(__name__)
CORS(app)

# Directory to store story files
BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)


# Backend Functions #

"""
/load

Load story file ID, content, summary, and plot essentials. 
Returns 400 if filename or ID is missing, 404 if file not found, and 500 for other errors.
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
            story_id = data.get("story_id")
            memory_cursor = data.get("memory_cursor")
            content = data.get("content", "")
            summary = data.get("summary", "None.")
            plot_essentials = data.get("plot_essentials", "None.")
    except Exception as e:
        # Internal Server Error
        return jsonify({"error": str(e)}), 500

    if not story_id:
        return jsonify({"error": "Story ID missing from file."}), 400

    return jsonify({"story_id": story_id, "memory_cursor": memory_cursor, "content": content, 
                    "summary": summary, "plot_essentials": plot_essentials})

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
    story_id = data.get('story_id')
    memory_cursor = data.get('memory_cursor')

    if not filename:
        return jsonify({"error": "Filename is required"}), 400
    if not story_id:
        return jsonify({"error": "Story ID is required"}), 400
    
    path = os.path.join(BASE_DIR, filename)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"story_id": story_id, "memory_cursor": memory_cursor, "content": content, "summary": summary, 
                   "plot_essentials": plot_essentials}, 
                  f, ensure_ascii=False, indent=2)

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

    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400
    
    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    story_id = data.get('story_id')
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400

    # Validate environment configuration
    if not api_url or not api_key:
        return jsonify({"error": "API_URL or API_KEY not set."}), 500
    
    full_prompt = content

    memories = database.get_relevant_memories(content, story_id)

    if (memories != []):
        memory_block = "\n".join(memories)

        full_prompt = f"""
        Relevant Memories:
        {memory_block}

        Recent Story:
        {content}
        """

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": GENERATION_SYS_PROMPT},
            {"role": "user", "content": full_prompt}
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

    print(f"[Backend] Total API call tokens used: {result['usage']['total_tokens']}", flush=True)

    if not continued_content or continued_content.strip() == "":
        return jsonify({"error": "AI API returned empty content."}), 500

    trimmed = utils.trim_incomplete_sentences(continued_content)

    return jsonify({"continued_content": trimmed})

"""
/summarize

Summarize story using external or local AI API.
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
    
    local = data.get('local')

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    new_summary = ""

    if (local and local == True):
        # Local summarization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.2
            },
            "stream": False
        })

        if response.status_code == 200:
            data = response.json()

            new_summary = data.get("message", {}).get("content", "").strip()

            total_tokens = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

            print(f"[Backend] Total local tokens used: {total_tokens}", flush=True)
        else:
            return {"error": response.text}, response.status_code
    # Default to cloud  
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "temperature": 0.2
        }

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_summary = result["choices"][0]["message"]["content"]

        print(f"[Backend] Total API call tokens used: {result['usage']['total_tokens']}", flush=True)

    trimmed = utils.trim_incomplete_sentences(new_summary)

    return jsonify({"summary": trimmed})

@app.route('/api/memorize', methods=['POST'])
def memorize():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    if not content or content.strip() == "":
        return jsonify({"error": "Empty content."}), 400
    
    local = data.get('local')

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    story_id = data.get('story_id')
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    
    new_memory = ""

    if (local and local == True):
        # Local memorization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "num_predict": 200,
                "temperature": 0.0
            },
            "stream": False
        })

        if response.status_code == 200:
            data = response.json()

            new_memory = data.get("message", {}).get("content", "").strip()

            total_tokens = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

            print(f"[Backend] Total local tokens used: {total_tokens}", flush=True)
        else:
            return {"error": response.text}, response.status_code
    # Default to cloud
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "temperature": 0.0,
            "max_tokens": 200
        }

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_memory = result["choices"][0]["message"]["content"]

        print(f"[Backend] Total API call tokens used: {result['usage']['total_tokens']}", flush=True)

    trimmed = utils.trim_incomplete_sentences(new_memory)

    database.create_memory(story_id, trimmed)

    return jsonify({"memory": trimmed})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)