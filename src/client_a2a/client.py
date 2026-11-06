"""Client A2A pour outline_agent.

Parle le protocole A2A (JSON-RPC via a2a-sdk) exactement comme routing_agent,
avec un fallback HTTP si nécessaire. Expose une API synchrone et asynchrone.
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from dataclasses import dataclass

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import AgentCard, Message, Part, Role, SendMessageRequest, Task

from .configs import AGENT_URL, CLIENT_TIMEOUT, LOG


@dataclass(frozen=True)
class OutlineResult:
    """Résultat normalisé d'une génération d'outline."""

    text: str
    raw_task: Task | dict | None = None


class OutlineClient:
    """Client A2A pour l'agent outline.

    Usage :
        client = OutlineClient()  # utilise AGENT_URL depuis configs
        text = await client.generate_outline("Intelligence artificielle")
        # ou synchrone :
        text = client.generate_outline_sync("IA")
    """

    def __init__(self, agent_url: str | None = None, timeout: int | None = None) -> None:
        self.agent_url: str = (agent_url or AGENT_URL).rstrip("/")
        self.timeout: int = timeout or CLIENT_TIMEOUT
        self._card: AgentCard | None = None

    # ------------------------------------------------------------------ #
    # Agent Card
    # ------------------------------------------------------------------ #
    async def get_agent_card(self) -> AgentCard:
        if self._card is not None:
            return self._card
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            resolver = A2ACardResolver(http, self.agent_url)
            card = await resolver.get_agent_card()
            self._card = card
            LOG.info("Agent card résolue : %s (%s)", card.name, card.version)
            return card

    def get_agent_card_sync(self) -> AgentCard:
        return asyncio.run(self.get_agent_card())

    # ------------------------------------------------------------------ #
    # Health
    # ------------------------------------------------------------------ #
    async def health_check(self) -> bool:
        url = f"{self.agent_url}/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as http:
                resp = await http.get(url)
                return resp.status_code == 200
        except Exception:  # noqa: BLE001
            LOG.exception("Health check échoué pour %s", url)
            return False

    # ------------------------------------------------------------------ #
    # Core : envoi A2A
    # ------------------------------------------------------------------ #
    async def _send_a2a(self, prompt: str) -> Task:
        card = await self.get_agent_card()

        httpx_client = httpx.AsyncClient(timeout=self.timeout)
        try:
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            a2a_client = factory.create(card)

            message = Message(
                role=Role.ROLE_USER,
                parts=[Part(text=prompt)],
                message_id=str(uuid.uuid4()),
            )
            request = SendMessageRequest(message=message)

            # SDK 1.x : send_message est un générateur async
            send_result = a2a_client.send_message(request)
            if inspect.isawaitable(send_result):
                send_result = await send_result  # type: ignore[no-redef]

            task: Task | None = None
            if hasattr(send_result, "__aiter__"):
                async for event in send_result:  # type: ignore[attr-defined]
                    if hasattr(event, "task") and getattr(event, "task", None):
                        task = event.task  # type: ignore[attr-defined]
                    elif isinstance(event, Task):
                        task = event
                    elif hasattr(event, "result"):
                        task = event.result
            else:
                if isinstance(send_result, Task):
                    task = send_result
                elif hasattr(send_result, "task"):
                    task = send_result.task
                else:
                    task = send_result  # type: ignore[assignment]

            if task is None:
                raise RuntimeError("Aucune Task retournée par l'agent A2A")
            return task
        finally:
            await httpx_client.aclose()

    @staticmethod
    def _extract_text(task: Task | dict) -> str:
        """Extrait le texte final d'une Task A2A (robuste aux variantes SDK)."""
        # Protobuf Task
        try:
            if hasattr(task, "status") and getattr(task.status, "message", None):
                msg = task.status.message  # type: ignore[attr-defined]
                if msg and getattr(msg, "parts", None):
                    texts = [p.text for p in msg.parts if getattr(p, "text", None)]
                    if texts:
                        return "\n".join(texts)
            # history
            if hasattr(task, "history") and task.history:
                last = task.history[-1]  # type: ignore[attr-defined]
                if getattr(last, "parts", None):
                    texts = [p.text for p in last.parts if getattr(p, "text", None)]
                    if texts:
                        return "\n".join(texts)
            # artifacts
            if hasattr(task, "artifacts") and task.artifacts:
                for art in task.artifacts:  # type: ignore[attr-defined]
                    if getattr(art, "parts", None):
                        texts = [p.text for p in art.parts if getattr(p, "text", None)]
                        if texts:
                            return "\n".join(texts)
        except Exception:  # noqa: BLE001
            LOG.debug("Extraction protobuf échouée, tentative dict", exc_info=True)

        # dict / JSON
        if isinstance(task, dict):
            for key in ("status", "history", "artifacts"):
                val = task.get(key)
                if isinstance(val, dict) and "message" in val:
                    parts = val["message"].get("parts", [])
                    texts = [p.get("text", "") for p in parts if p.get("text")]
                    if texts:
                        return "\n".join(texts)
                if isinstance(val, list) and val:
                    last = val[-1]
                    if isinstance(last, dict) and "parts" in last:
                        texts = [p.get("text", "") for p in last["parts"] if p.get("text")]
                        if texts:
                            return "\n".join(texts)

        # Fallback : sérialise
        if hasattr(task, "model_dump_json"):
            try:
                return task.model_dump_json()  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001, S110
                pass
        return str(task)

    # ------------------------------------------------------------------ #
    # API publique
    # ------------------------------------------------------------------ #
    async def generate_outline(self, topic: str) -> OutlineResult:
        """Génère un outline via A2A. Lève en cas d'échec."""
        topic = topic.strip()
        if not topic:
            raise ValueError("Le sujet ne peut pas être vide")
        LOG.info("generate_outline topic=%r url=%s", topic[:80], self.agent_url)
        task = await self._send_a2a(topic)
        text = self._extract_text(task).strip()
        if not text:
            text = "Aucune réponse de l'agent."
        return OutlineResult(text=text, raw_task=task)

    def generate_outline_sync(self, topic: str) -> OutlineResult:
        return asyncio.run(self.generate_outline(topic))

    # alias compat
    async def send_prompt(self, prompt: str) -> str:
        result = await self.generate_outline(prompt)
        return result.text

    def send_prompt_sync(self, prompt: str) -> str:
        return self.generate_outline_sync(prompt).text


# ------------------------------------------------------------------ #
# Helpers fonctionnels (compat avec l'ancien clientA2A.py)
# ------------------------------------------------------------------ #
_default_client: OutlineClient | None = None


def get_client(agent_url: str | None = None) -> OutlineClient:
    global _default_client
    if agent_url:
        return OutlineClient(agent_url=agent_url)
    if _default_client is None:
        _default_client = OutlineClient()
    return _default_client


def send_prompt(prompt: str, agent_url: str | None = None) -> str:
    """Fonction synchrone compat : envoie un prompt et retourne le texte."""
    client = get_client(agent_url)
    return client.send_prompt_sync(prompt)


async def send_prompt_async(prompt: str, agent_url: str | None = None) -> str:
    client = get_client(agent_url)
    return await client.send_prompt(prompt)
