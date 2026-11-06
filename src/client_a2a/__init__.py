"""Client A2A — package outline.

Structure modulaire alignée sur outline_agent :

    configs.py  → env, LOG, AGENT_URL (miroir agent/configs.py)
    client.py   → OutlineClient (A2A JSON-RPC)
    ui_components.py → rendu Streamlit pur
    ui.py / app.py   → app Streamlit (point d'entrée)
"""

from .client import OutlineClient, OutlineResult, get_client, send_prompt
from .configs import AGENT_URL, HOST, LOG, PORT, get_agent_url

__all__ = [
    "AGENT_URL",
    "HOST",
    "LOG",
    "PORT",
    "OutlineClient",
    "OutlineResult",
    "get_agent_url",
    "get_client",
    "send_prompt",
]


def main() -> None:
    import asyncio

    from .client import OutlineClient

    async def _run() -> None:
        print("Client A2A Outline — tape 'quit' pour quitter.")
        print(f"Agent: {AGENT_URL}")
        client = OutlineClient()
        while True:
            topic = input("Sujet: ").strip()
            if topic.lower() in {"quit", "exit", "q"}:
                break
            if not topic:
                continue
            try:
                res = await client.generate_outline(topic)
                print("\n--- Outline ---\n" + res.text + "\n")
            except Exception as exc:  # noqa: BLE001
                print(f"Erreur: {exc}")

    asyncio.run(_run())
