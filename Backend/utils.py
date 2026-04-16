import re
import requests

def trim_incomplete_sentences(text):
    last_period_index = text.rfind('.')
    if last_period_index != -1:
        return text[:last_period_index + 1]
    return text

def trim_content_to_length(text, max_length=300):
    if len(text) <= max_length:
        return text

    # Get recent content up to max_length
    trimmed = text[-max_length:]

    # Remove partial sentence at the start
    start_match = re.search(r'[.!?]\s+', trimmed)
    if start_match:
        trimmed = trimmed[start_match.end():]

    return trimmed.strip()

def call_ai_api(api_url, headers, payload):
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)

        # Try to parse JSON
        try:
            data = response.json()
        except Exception:
            data = None

        # Handle HTTP errors explicitly
        if response.status_code == 400:
            message = "Bad request."

            if data and "error" in data:
                message = data["error"].get("message", message)

                # Check for common model-related error messages (e.g. "model not found")
                if "model" in message.lower():
                    return None, (f"Model error: {message}", 400)

            return None, (message, 400)

        if response.status_code == 429:
            return None, ("Rate limit exceeded. Wait or increase rate limit.", 429)

        if response.status_code == 401:
            return None, ("Unauthorized. Check your API key.", 401)

        if response.status_code >= 500:
            return None, ("AI service is currently unavailable.", 503)

        if response.status_code != 200:
            return None, (f"Unexpected error: {response.text}", response.status_code)

        # Parse JSON
        try:
            return response.json(), None
        except Exception:
            return None, ("Invalid response from AI API.", 500)

    except requests.exceptions.Timeout:
        return None, ("Request timed out. Please try again.", 504)

    except requests.exceptions.ConnectionError:
        return None, ("Failed to connect to AI service.", 503)

    except Exception as e:
        return None, (f"Unexpected error: {str(e)}", 500)