import re

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