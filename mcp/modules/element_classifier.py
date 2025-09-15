import json
import requests
from config import OPEN_ROUTER_KEY

# Standard element types for classification
ELEMENT_TYPES = [
    "UI_COMPONENT",     # Buttons, inputs, menus, panels
    "PROCESS_STEP",     # Workflow steps, operations
    "DATA_STORE",       # Databases, files, caches
    "ACTION",           # User actions, system actions
    "DECISION",         # If/then logic, branching
    "CONNECTOR",        # Arrows, lines, relationships
    "ACTOR",            # Users, systems, roles
    "CONTAINER",        # Groups, boundaries, sections
    "ANNOTATION",       # Labels, notes, comments
    "OTHER"             # Fallback category
]

def is_valid_classification_input(text: str, max_length: int = 200) -> tuple:
    """
    Validate if input is worth classifying before making API call.

    Returns:
        (is_valid, reason_if_invalid)
    """
    # Check length (rough token estimate: 1 token ≈ 4 chars)
    if len(text) > max_length:
        return False, f"Input too long ({len(text)} chars, max {max_length})"

    # Check for meaningful content
    if not has_meaningful_words(text):
        return False, "Input appears to be gibberish or non-meaningful"

    return True, ""

def has_meaningful_words(text: str) -> bool:
    """Check if text contains actual words vs gibberish"""
    import re

    # Remove non-alphanumeric except spaces and common punctuation
    clean_text = re.sub(r'[^\w\s\-\.,:;!?]', ' ', text)
    words = clean_text.split()

    if not words:
        return False

    # Check for patterns that suggest real words
    meaningful_count = 0
    for word in words:
        word = word.lower().strip('.,!?;:-')
        if len(word) < 2:
            continue

        # Real words typically have vowels and reasonable letter patterns
        if has_vowels(word) and not is_repetitive(word):
            meaningful_count += 1

    # At least 50% of words should appear meaningful
    return meaningful_count >= len(words) * 0.5

def has_vowels(word: str) -> bool:
    """Check if word contains vowels (basic word indicator)"""
    return any(c in 'aeiouAEIOU' for c in word)

def is_repetitive(word: str) -> bool:
    """Check if word is just repeated characters (like 'xxxxx')"""
    if len(word) <= 2:
        return False
    return len(set(word.lower())) <= 2

def classify_element(element_label: str) -> dict:
    """
    Classify a diagram element label into a standard category using OpenRouter API.

    Args:
        element_label: The text label to classify

    Returns:
        dict: Contains 'classification', 'confidence', 'token_usage', and 'error' fields
    """

    if not element_label or not element_label.strip():
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': 'Empty element label provided'
        }

    # Early validation to avoid wasting API calls on gibberish
    is_valid, reason = is_valid_classification_input(element_label.strip())
    if not is_valid:
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': f'Input rejected: {reason}'
        }

    # Construct classification prompt
    prompt = f"""Classify this diagram element label into one of these categories:
{', '.join(ELEMENT_TYPES)}

Element label: "{element_label}"

Return only the category name from the list above. Consider:
- UI_COMPONENT: buttons, forms, menus, screens, inputs
- PROCESS_STEP: steps in a workflow, operations, tasks
- DATA_STORE: databases, files, storage, caches
- ACTION: user actions, system actions, events
- DECISION: if/then logic, conditions, choices
- CONNECTOR: arrows, links, relationships
- ACTOR: users, people, systems, roles
- CONTAINER: groups, sections, boundaries
- ANNOTATION: labels, notes, explanations
- OTHER: anything that doesn't fit above

Category:"""

    try:
        # OpenRouter API call
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 20
            },
            timeout=30
        )

        if response.status_code != 200:
            return {
                'classification': 'OTHER',
                'confidence': 0.0,
                'token_usage': 0,
                'error': f'API request failed with status {response.status_code}: {response.text}'
            }

        result = response.json()

        # Extract classification from response
        if 'choices' not in result or not result['choices']:
            return {
                'classification': 'OTHER',
                'confidence': 0.0,
                'token_usage': 0,
                'error': 'No choices in API response'
            }

        classification_text = result['choices'][0]['message']['content'].strip().upper()

        # Validate classification is in our allowed types
        if classification_text in ELEMENT_TYPES:
            classification = classification_text
            confidence = 0.9
        else:
            # Try to find partial match
            for element_type in ELEMENT_TYPES:
                if element_type in classification_text:
                    classification = element_type
                    confidence = 0.7
                    break
            else:
                classification = 'OTHER'
                confidence = 0.5

        # Extract token usage
        token_usage = result.get('usage', {}).get('total_tokens', 0)

        return {
            'classification': classification,
            'confidence': confidence,
            'token_usage': token_usage,
            'error': None
        }

    except requests.exceptions.Timeout:
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': 'API request timed out after 30 seconds'
        }
    except requests.exceptions.RequestException as e:
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': f'Network error: {str(e)}'
        }
    except json.JSONDecodeError as e:
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': f'Invalid JSON response: {str(e)}'
        }
    except Exception as e:
        return {
            'classification': 'OTHER',
            'confidence': 0.0,
            'token_usage': 0,
            'error': f'Unexpected error: {str(e)}'
        }