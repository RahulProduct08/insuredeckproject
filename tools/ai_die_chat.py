"""
tools/ai_die_chat.py — AI-DIE (AI Digital Insurance Engine) chat service.

Wraps the Anthropic Claude API with the AI-DIE system prompt to power the
insurance sales simulation chat interface.
"""

import os
import anthropic

_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "prompts", "ai_die_system.txt"
)

_SYSTEM_PROMPT_CACHE = None

def _load_system_prompt() -> str:
    """Load and cache system prompt to avoid repeated disk I/O on every API call."""
    global _SYSTEM_PROMPT_CACHE
    if _SYSTEM_PROMPT_CACHE is None:
        with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
            _SYSTEM_PROMPT_CACHE = f.read()
    return _SYSTEM_PROMPT_CACHE


def send_message(conversation_history: list, user_message: str) -> str:
    """
    Send a user message to AI-DIE and return the assistant reply.

    Args:
        conversation_history: List of prior messages in
            [{"role": "user"|"assistant", "content": "..."}] format.
        user_message: The new user message to append.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
        anthropic.APIError: If API call fails
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()

    messages = conversation_history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        temperature=0,
        timeout=30,
    )

    if not response.content or not response.content[0].text:
        raise ValueError("Empty response from Anthropic API")

    return response.content[0].text
