"""Évaluation du clientA2A — métriques sans modifier clientA2A.py.

Lance :
    uv run python -m evaluation.evaluate
    uv run python -m evaluation.evaluate --live  # requêtes réelles (optionnel)

Mesure :
- latence (p50/p95)
- taux d'erreur (Error / Request failed / No response)
- qualité minimale (réponse non vide, longueur)
Entrées : prompts de référence inspirés du cas d'usage outline.
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass

import clientA2A

# Prompts de référence — même domaine que outline_agent INSTRUCTION (4-6 sections)
REFERENCE_PROMPTS = [
    "Donne-moi un outline pour un article sur l'IA dans l'éducation",
    "Outline : le futur du travail à distance en 6 sections",
    "Plan d'article : les énergies renouvelables en 2030",
    "Propose un outline pour un billet sur le lancement d'un podcast",
    "Outline blog post : la cybersécurité pour les TPE",
]


@dataclass
class EvalResult:
    prompt: str
    response: str
    latency_s: float
    ok: bool
    kind: str  # ok | error | request_failed | empty_fallback


def classify(response: str) -> tuple[bool, str]:
    if response.startswith("Request failed"):
        return False, "request_failed"
    if response.startswith("Error"):
        return False, "error"
    if response == "No response from agent." or not response.strip():
        return False, "empty_fallback"
    return True, "ok"


def run_evaluation(live: bool = False, timeout: float = 30.0) -> dict:
    """Exécute l'évaluation. Si live=False, mocke clientA2A pour rester offline."""
    results: list[EvalResult] = []

    if not live:
        # Simulation offline : mock déterministe (pas d'appel réseau)
        from unittest.mock import MagicMock, patch

        fake = MagicMock(status_code=200, text="ok")
        fake.json.return_value = {"response": "1. Introduction\n2. Contexte\n3. Développement\n4. Conclusion"}
        patcher = patch("clientA2A.requests.post", return_value=fake)
        patcher.start()

    try:
        for prompt in REFERENCE_PROMPTS:
            t0 = time.perf_counter()
            resp = clientA2A.send_prompt(prompt)
            latency = time.perf_counter() - t0
            ok, kind = classify(resp)
            results.append(EvalResult(prompt, resp, latency, ok, kind))
    finally:
        if not live:
            patcher.stop()  # type: ignore[possibly-undefined]

    latencies = [r.latency_s for r in results]
    by_kind: dict[str, int] = {}
    for r in results:
        by_kind[r.kind] = by_kind.get(r.kind, 0) + 1

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r.ok),
        "error_rate": 1 - sum(1 for r in results if r.ok) / len(results) if results else 0,
        "by_kind": by_kind,
        "latency_p50": statistics.median(latencies) if latencies else 0,
        "latency_p95": sorted(latencies)[int(0.95 * len(latencies))] if latencies else 0,
        "latency_mean": statistics.mean(latencies) if latencies else 0,
        "results": results,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue clientA2A.py")
    parser.add_argument("--live", action="store_true", help="appels réels au serveur")
    args = parser.parse_args()

    summary = run_evaluation(live=args.live)

    print(f"=== Evaluation clientA2A (live={args.live}) ===")
    print(f"Total: {summary['total']}  OK: {summary['ok']}  error_rate: {summary['error_rate']:.0%}")
    print(f"by_kind: {summary['by_kind']}")
    print(f"latency mean={summary['latency_mean']:.3f}s p50={summary['latency_p50']:.3f}s p95={summary['latency_p95']:.3f}s")
    print("--- détails ---")
    for r in summary["results"]:
        preview = r.response[:120].replace("\n", " | ")
        print(f"[{r.kind:14s}] {r.latency_s:.3f}s | {r.prompt[:50]:50s} -> {preview}")


if __name__ == "__main__":
    main()
