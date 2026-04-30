from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import re
import os
from default_prompts import GENERATION_SYS_PROMPT, SUMMARIZATION_SYS_PROMPT, MEMORY_SYS_PROMPT
import utils
import database

# Initialize the database
database.init_db()

# Check if local AI is enabled via Docker compose environment variable 
# Default to false if not set
LOCAL_AI_ENABLED = os.getenv("LOCAL_AI_ENABLED", "false") == "true"

# Local Ollama model API endpoint and model
OLLAMA_URL = "http://ai:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"

api_url = os.getenv("API_URL")
api_key = os.getenv("API_KEY")
api_main_model = os.getenv("API_MAIN_MODEL", None)
api_mem_model = os.getenv("API_MEM_MODEL", None)

app = Flask(__name__)
CORS(app)

# Directory to store story files
BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)


# Backend Routes #


"""
/config

Returns configuration settings.
"""
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        "local_ai_enabled": LOCAL_AI_ENABLED,
        "main_model": api_main_model,
        "mem_model": api_mem_model
    })

"""
/load

Load story file by filename. 
Returns 400 if filename or story_id is missing or invalid, 
404 if file not found, and 500 for other errors.
"""
@app.route('/api/load', methods=['GET'])
def load_file():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"error": "Filename is required."}), 400
    
    # Basic validation to prevent directory traversal or invalid filenames.
    # Only allow .json files.
    if not re.match(r'^[a-zA-Z0-9_-]+\.json$', filename):
        return jsonify({"error": "Invalid filename."}), 400

    path = os.path.join(BASE_DIR, filename)

    # Ensure the real path is within the BASE_DIR to prevent directory traversal
    real_path = os.path.realpath(path)
    if not real_path.startswith(os.path.realpath(BASE_DIR)):
        return jsonify({"error": "Invalid path."}), 400

    # Ensure file exists before attempting to open
    if not os.path.exists(path):
        return jsonify({"error": "File not found."}), 404

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            story_id = data.get("story_id")
            instructions = data.get("instructions", '')
            content = data.get("content", '')
            summary = data.get("summary", '')
            story_essentials = data.get("story_essentials", '')
            memory_cursor = data.get("memory_cursor", 0)
            summary_cursor = data.get("summary_cursor", 0)
            context_cards = data.get("context_cards", [])
    except Exception as e:
        # Internal Server Error
        return jsonify({"error": str(e)}), 500

    # Validate story ID
    if not story_id:
        return jsonify({"error": "Story ID missing from file."}), 400
    # Check that ID is a positive integer. Separate check for bool as python counts True and False as int.
    if not isinstance(story_id, int) or isinstance(story_id, bool) or story_id <= 0:
        return jsonify({"error": "Invalid story ID. ID must be a positive integer."}), 400

    return jsonify({"story_id": story_id, "instructions": instructions, "content": content, 
                    "summary": summary, "story_essentials": story_essentials, "memory_cursor": memory_cursor,
                    "summary_cursor":summary_cursor, "context_cards": context_cards})

"""
/save

Save story to file. Valid filename and story_id are required. 
Returns 400 if filename or story_id is missing. 
"""
@app.route('/api/save', methods=['POST'])
def save_file():
    data = request.json
    filename = data.get("filename")
    story_id = data.get("story_id")

    # Validate story ID
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    if not isinstance(story_id, int) or isinstance(story_id, bool) or story_id <= 0:
        return jsonify({"error": "Invalid story ID. ID must be a positive integer."}), 400

    # Validate file
    if not filename:
        return jsonify({"error": "Filename is required."}), 400
    
    # Basic validation to prevent directory traversal or invalid filenames.
    # Only allow .json files.
    if not re.match(r'^[a-zA-Z0-9_-]+\.json$', filename):
        return jsonify({"error": "Invalid filename."}), 400
    
    path = os.path.join(BASE_DIR, filename)

    # Ensure the real path is within the BASE_DIR to prevent directory traversal
    real_path = os.path.realpath(path)
    if not real_path.startswith(os.path.realpath(BASE_DIR)):
        return jsonify({"error": "Invalid path."}), 400
    
    # Create a backup of existing file. Only keep one backup per file.
    if os.path.exists(path):
        # Build backup filename (story.json -> story_backup.json)
        base, ext = os.path.splitext(filename) # Get base name without extension
        backup_filename = f"{base}_backup.json"
        backup_path = os.path.join(BASE_DIR, backup_filename)

        # Ensure backup path is also safe
        real_backup_path = os.path.realpath(backup_path)
        if not real_backup_path.startswith(os.path.realpath(BASE_DIR)):
            return jsonify({"error": "Invalid backup path."}), 400

        # If backup already exists, remove it (only keep one backup)
        if os.path.exists(backup_path):
            os.remove(backup_path)

        # Rename current file to backup
        os.rename(path, backup_path)

    # Get rest of saved data
    instructions = data.get("instructions", '')
    content = data.get("content", '')
    summary = data.get("summary", '')
    story_essentials = data.get("story_essentials", '')
    memory_cursor = data.get("memory_cursor", 0)
    summary_cursor = data.get("summary_cursor", 0)
    context_cards = data.get("context_cards", [])

    # Save new file
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"story_id": story_id, "instructions": instructions, "content": content, 
                   "summary": summary, "story_essentials": story_essentials, "memory_cursor": memory_cursor, 
                   "summary_cursor": summary_cursor, "context_cards": context_cards}, 
                  f, ensure_ascii=False, indent=2)

    return jsonify({"message": "File saved as " + filename + "."})

"""
/continue

Continue story using external AI API. 
Returns 400 for missing/invalid JSON, empty content, or missing model; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
@app.route('/api/continue', methods=['POST'])
def continue_story():
    # Validate request JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    recent_story = data.get('recent_story')
    if not recent_story or recent_story.strip() == "":
        return jsonify({"error": "Empty story content."}), 400
    
    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    story_id = data.get('story_id')
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    
    user_instructions = data.get('instructions')
    story_essentials = data.get('story_essentials', 'None.')
    summary = data.get('summary', 'None.')
    context_cards = data.get('context_cards', 'None.')

    top_p = data.get('top_p', 0.9)
    temperature = data.get('temperature', 0.8)
    max_tokens = data.get('max_tokens', 200)

    # Validate environment configuration
    if not api_url or not api_key:
        return jsonify({"error": "API_URL or API_KEY not set."}), 500
    
    # Get relevant memories for recent content
    relevant_memories = database.get_relevant_memories(recent_story[-2000:], story_id, 2)

    # Get most recent memories for story
    recent_memories = database.get_recent_memories(story_id, 2)

    # Combine and remove duplicate memories
    unique_memories = list(set(relevant_memories + recent_memories))

    memory_block = "\n".join(unique_memories) or "None."
    
    # Context ordered based on which content is most likely to stay static (unedited).
    # This will increase rate of cache hits in API call -> cheaper responses (if supported by API provider).
    full_prompt = (
        "[Story Essentials]\n" + story_essentials +
        "\n\n[Story Summary]\n" + summary +
        "\n\n[Past Memories]\n" + memory_block +
        "\n\n[Relevant Context]\n" + context_cards +
        "\n\n[Recent Story]\n" + recent_story
    )
    
    full_instructions = GENERATION_SYS_PROMPT

    if (user_instructions.strip() != ''):
        full_instructions = (f"{GENERATION_SYS_PROMPT}\nSTORYTELLING:\n\n{user_instructions}")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": full_instructions},
            {"role": "user", "content": full_prompt}
        ],
        "max_tokens": max_tokens,
        "top_p": top_p,
        "temperature": temperature,
        "presence_penalty": 0.3, # Increases the likelihood of introducing new content vs repeating existing content
        "frequency_penalty": 0.3 # Decreases the likelihood of repeating words or phrases
    }

    # Disable "thinking" phase for DeepSeek models to reduce output token use 
    # -> cheaper responses.
    # Can be removed for better storytelling quality if cost is not a concern.
    # May become redundant if model names are changed by API provider.
    if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        payload["thinking"] = {"type": "disabled"}

    # Call external AI API with error handling
    result, error = utils.call_ai_api(api_url, headers, payload)

    if error:
        message, status = error
        return jsonify({"error": message}), status

    continued_content = result["choices"][0]["message"]["content"]

    if not continued_content or continued_content.strip() == "":
        return jsonify({"error": "AI API returned empty content."}), 500

    trimmed = utils.trim_incomplete_sentences(continued_content)

    full_context = '{---SYSTEM---}\n' + full_instructions + '\n\n{---USER---}\n\n' + full_prompt

    return jsonify({"continued_content": trimmed, "tokens_total": result['usage']['total_tokens'],
                    "full_context": full_context})

"""
/summarize

Summarize story using external or local AI API.
Returns 400 for missing/invalid JSON, empty content, or missing model;
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty summary.
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
    tokens_total = -1

    if (local and local == True and LOCAL_AI_ENABLED):
        # Local summarization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.2, # Low temperature for summary creation
                "num_predict": 1000 # Token limit to prevent unnecessarily responses
            },
            "stream": False
        })

        if response.status_code == 200:
            data = response.json()

            new_summary = data.get("message", {}).get("content", "").strip()
            tokens_total = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

        else:
            return jsonify({"error": response.text}), response.status_code
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
            "temperature": 0.2,
            "max_tokens": 1000
        }

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_summary = result["choices"][0]["message"]["content"]

        tokens_total = result['usage']['total_tokens']

    trimmed = utils.trim_incomplete_sentences(new_summary)

    return jsonify({"summary": trimmed, "tokens_total": tokens_total})

"""
/memorize

Creates a memory using local or cloud AI. Memory is stored in the database.
Returns 400 for missing/invalid JSON, empty content, or missing model or story_id; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
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
    tokens_total = -1

    if (local and local == True and LOCAL_AI_ENABLED):
        # Local memorization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.0, # Low temperature for best consistency
                "num_predict": 200
            },
            "stream": False
        })

        if response.status_code == 200:
            data = response.json()

            new_memory = data.get("message", {}).get("content", "").strip()

            # Some models often include metatext (e.g. "Here are the created memories:") in their output
            # even when explicitly instructed not to. The commented out function below removes the first
            # line of the output and can be used if encountering issues with metatext generation.
            # It was useful with llama:3 but switching to llama:3.1 seemed to lessen the issue.
            # 
            # new_memory = "\n".join(new_memory.splitlines()[1:]).lstrip("\n")

            tokens_total = data.get("prompt_eval_count", 0) + data.get("eval_count", 0)

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

        tokens_total = result['usage']['total_tokens']

    trimmed = utils.trim_incomplete_sentences(new_memory)

    database.create_memory(story_id, trimmed)

    return jsonify({"memory": trimmed, "tokens_total": tokens_total})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
