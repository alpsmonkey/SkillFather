"""LLM client - encapsulates API calls, retry, timeout, and SSL configuration.

Extracted from analyzer.py to decouple analysis logic from LLM transport.
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from skillfather.config import LLMConfig

# Environment variable: set SKILLFATHER_SSL_VERIFY=0 to disable SSL verification
# (useful for corporate proxies with self-signed certs). Default is verify=True.
_SSL_VERIFY = os.environ.get("SKILLFATHER_SSL_VERIFY", "1") != "0"

# Default request timeout in seconds
_DEFAULT_TIMEOUT = 60

# Max retry attempts for transient failures
_MAX_RETRIES = 2


def call_llm(system_prompt: str, user_prompt: str, config: LLMConfig) -> str:
    """Call OpenAI-compatible chat completion API.

    Args:
        system_prompt: System message content.
        user_prompt: User message content.
        config: LLM configuration (API key, base URL, model, etc.).

    Returns:
        Assistant message content string.

    Raises:
        RuntimeError: On API call failure or unexpected response format.
    """
    url = f"{config.base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    # SSL context: verify by default; opt-out via SKILLFATHER_SSL_VERIFY=0
    if _SSL_VERIFY:
        ctx = ssl.create_default_context()
    else:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=_DEFAULT_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except urllib.error.URLError as e:
            last_error = e
            if attempt < _MAX_RETRIES:
                continue
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected LLM response format: {e}") from e

    raise RuntimeError(f"LLM API call failed after {_MAX_RETRIES + 1} attempts: {last_error}") from last_error
