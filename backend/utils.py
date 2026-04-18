import re
import requests

"""
Utility functions for AI Storyteller backend, including:
- trim_incomplete_sentences: Trims text to the last complete sentence. Useful due to
  AI models sometimes returning incomplete sentences at the end of generated content.
- call_ai_api: Makes a POST request to an AI API with error handling for various scenarios
  (HTTP errors, timeouts, connection issues, and unexpected exceptions). 
  Returns either the API response data or an error message with an appropriate status code.
"""
def trim_incomplete_sentences(text):
    last_period_index = text.rfind('.')
    if last_period_index != -1:
        return text[:last_period_index + 1]
    return text

def call_ai_api(api_url, headers, payload):
    try:
        # Call external AI API with 10-second timeout
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

            return None, (message, 400)

        if response.status_code == 429:
            return None, ("Rate limit exceeded. Wait or increase rate limit.", 429)

        if response.status_code == 401:
            return None, ("Unauthorized. Check your API key and permissions.", 401)

        if response.status_code >= 500:
            return None, ("AI service is currently unavailable.", 503)

        if response.status_code != 200:
            return None, (f"Unexpected error: {response.text}", response.status_code)

        # Return data if valid, otherwise return error
        if (data):
            return data, None
        else:
            return None, ("Invalid response from AI API.", 500)

    except requests.exceptions.Timeout:
        return None, ("Request timed out. Please try again.", 504)

    except requests.exceptions.ConnectionError:
        return None, ("Failed to connect to AI service.", 503)

    except Exception as e:
        return None, (f"Unexpected error: {str(e)}", 500)