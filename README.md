# Client A2A — Outline Agent

Client **uniquement** (pas de serveur) pour l'agent `outline-agent`.  
Structure modulaire calquée sur `outline-agent`, configs alignées, UI Streamlit professionnelle.

## Structure

```
app-a2a/
├── ui.py                      # Point d'entrée Streamlit (streamlit run ui.py)
├── clientA2A.py               # CLI compat (python clientA2A.py)
├── .env.example               # Miroir outline_agent/.env
├── pyproject.toml
└── src/client_a2a/
    ├── __init__.py            # exports + CLI async
    ├── configs.py             # ← miroir outline_agent/configs.py (HOST, PORT, PUBLIC_URL, LOG, AGENT_URL)
    ├── client.py              # OutlineClient A2A (A2ACardResolver + ClientFactory)
    ├── ui_components.py       # rendu pur (styles, parse_outline)
    └── (ui.py orchestration à la racine)
```

## Configs — alignées sur outline_agent

`src/client_a2a/configs.py` reprend exactement :

- `MODEL_ID`, `OPENAI_API_KEY`, `BASE_URL`
- `HOST`, `PORT`, `PUBLIC_URL`
- `LOG` / `LOG_LEVEL` (même format)

Ajoute uniquement :

- `AGENT_URL` — résolue comme `AGENT_URL` env > `PUBLIC_URL` (normalisée `https://` si nue) > `http://HOST:PORT`
- `CLIENT_TIMEOUT` (défaut `60`), `CLIENT_RETRIES`

Le `.env` est interchangeable avec celui de l'agent.

## Installation

```bash
# Depuis app-a2a/
uv venv
uv sync
# ou
uv pip install -e .
```

## Lancer l'UI

```bash
uv run streamlit run ui.py
# ouvre http://localhost:8501
```

La sidebar permet de surcharger l'URL de l'agent et de tester `/health`.

## Lancer le CLI

```bash
uv run python clientA2A.py
# ou
uv run python -m client_a2a
```

## Variables d'environnement

Voir `.env.example`. L'agent doit tourner (`outline-agent/server.py` sur `PORT`).
