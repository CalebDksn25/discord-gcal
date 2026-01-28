import asyncio
import requests
from typing import Dict, List
from lib.prompts import OPENAI_SYSTEM_PROMPT, OPENAI_USER_PROMPT

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama2"  # Change to your preferred model (e.g., "neural-chat", "mistral")

class LLMError(Exception):
    """Raise this error for LLM related issues."""
    pass


def _generate_response_sync(messages: List[Dict[str, str]]) -> str:
    """Synchronous helper for making Ollama requests."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False, 
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["message"]["content"]

    except requests.exceptions.ConnectionError:
        raise LLMError(
            "LLM backend unavailable. "
            "Make sure Ollama is running with: `ollama serve`"
        )

    except requests.exceptions.Timeout:
        raise LLMError(
            "LLM request timed out. "
            "The model may be loading or under heavy load."
        )

    except requests.exceptions.RequestException as e:
        raise LLMError(f"LLM error: {e}")


async def get_ollama_response(user_input: str) -> str:
    """
    Get a response from Ollama using the same prompts as OpenAI.
    Runs the blocking request in an executor to avoid blocking the event loop.
    """
    # Prepare the user prompt by inserting the user input
    user_prompt = OPENAI_USER_PROMPT.replace("{{USER_INPUT}}", user_input)

    # Build the messages in OpenAI format
    messages = [
        {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # Run the blocking request in a thread pool
    loop = asyncio.get_event_loop()
    response_text = await loop.run_in_executor(
        None,
        _generate_response_sync,
        messages
    )

    return response_text