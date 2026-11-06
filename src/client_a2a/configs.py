"""Shim package : ré-exporte la config racine `configs.py`.

Garde `from configs import HOST, PORT` (clientA2A.py) et
`from src.client_a2a.configs import ...` interchangeables.
"""

from configs import (  # type: ignore[import-not-found]
    AGENT_URL,
    BASE_URL,
    CLIENT_RETRIES,
    CLIENT_TIMEOUT,
    HOST,
    LOG,
    MODEL_ID,
    OPENAI_API_KEY,
    PORT,
    PUBLIC_URL,
    get_agent_url,
)

__all__ = [
    "AGENT_URL",
    "BASE_URL",
    "CLIENT_RETRIES",
    "CLIENT_TIMEOUT",
    "HOST",
    "LOG",
    "MODEL_ID",
    "OPENAI_API_KEY",
    "PORT",
    "PUBLIC_URL",
    "get_agent_url",
]
