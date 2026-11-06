"""Point d'entrée Streamlit — construit AUTOUR de clientA2A.py sans le modifier.

- N'importe aucune logique métier nouvelle : appelle directement `clientA2A.send_prompt`
- Respecte son contrat : POST {"message": prompt} -> 200 {"response": ...}
  sinon "Error {code}: {text}" ou "Request failed: {e}" ou "No response from agent."
- N'ajoute rien dans clientA2A.py, ne le patch pas.

Lance avec :
    streamlit run ui.py
    uv run streamlit run ui.py
"""

from __future__ import annotations

import datetime
import time

import requests
import streamlit as st

import clientA2A
from configs import HOST, LOG, PORT
from src.client_a2a.ui_components import inject_styles, parse_outline, render_outline

# ------------------------------------------------------------------ #
# Page
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="Client A2A — Routing Agent",
    page_icon="◧",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

if "history" not in st.session_state:
    st.session_state.history: list[dict] = []
if "last_result" not in st.session_state:
    st.session_state.last_result: str | None = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt: str | None = None
if "last_latency" not in st.session_state:
    st.session_state.last_latency: float | None = None

# URL dure dans clientA2A.py (introspectée pour affichage, pas pour la réécrire)
CLIENT_URL = "https://server-a2a-routing-agent.onrender.com/message"
try:
    import inspect

    src = inspect.getsource(clientA2A.send_prompt)
    # extrait l'URL littérale si présente
    import re

    m = re.search(r'url\s*=\s*["\']([^"\']+)["\']', src)
    if m:
        CLIENT_URL = m.group(1)
except Exception:  # noqa: BLE001, S110
    pass

PAYLOAD_EXAMPLE = '{"message": "votre prompt"}'

EXAMPLES = [
    "Donne-moi un outline pour un article sur l'IA dans l'éducation",
    "Outline : le futur du travail à distance en 6 sections",
    "Plan d'article : les énergies renouvelables en 2030",
    "Propose un outline pour un billet sur le lancement d'un podcast",
]

# ------------------------------------------------------------------ #
# Sidebar — fidèle au contrat clientA2A.py
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown('<div class="sidebar-title">Client A2A</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-caption">UI Streamlit bâtie autour de <code>clientA2A.py</code><br>'
        "Même contrat, même URL, même payload.</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("Cible (lecture seule)")
    st.code(CLIENT_URL, language="text")
    st.caption(f"`configs.py` — HOST={HOST} PORT={PORT} · URL effective clientA2A ci-dessus (introspectée)")
    st.code(f'POST {CLIENT_URL}\nPayload: {PAYLOAD_EXAMPLE}\n200 -> {{"response": "..."}}', language="text")

    c1, c2 = st.columns(2)
    with c1:
        timeout = st.number_input("Timeout (s)", min_value=5, max_value=120, value=30, step=5)
    with c2:
        if st.button("Tester /health", use_container_width=True):
            # clientA2A n'expose pas /health, on teste la racine dérivée
            base = CLIENT_URL.rsplit("/message", 1)[0]
            health_url = base + "/health"
            with st.spinner("Test…"):
                try:
                    r = requests.get(health_url, timeout=int(timeout))
                    if r.status_code == 200:
                        st.success(f"200 — {r.text[:120]}")
                    else:
                        st.warning(f"{r.status_code} — {r.text[:120]}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Request failed: {exc}")

    st.divider()
    st.subheader("Exemples")
    for ex in EXAMPLES:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.prompt_value = ex

    st.divider()
    st.markdown(
        """<div class="meta">
        <strong>Contrat clientA2A.py</strong><br>
        <code>send_prompt(prompt: str) -> str</code><br>
        200 → <code>response.json()["response"]</code> ou "No response from agent."<br>
        !200 → "Error {code}: {text}"<br>
        exception → "Request failed: {e}"
        </div>""",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #
left, right = st.columns([1.55, 0.85], gap="large")

with left:
    st.title("Client A2A — Routing Agent")
    st.caption(
        "Saisis ton prompt — l'UI appelle exactement `clientA2A.send_prompt(prompt)` "
        "et affiche son retour tel quel (succès / Error / Request failed)."
    )

    default_prompt = st.session_state.get("prompt_value", "")
    prompt = st.text_area(
        "Prompt",
        value=default_prompt,
        height=120,
        placeholder="Ex : Donne-moi un outline pour un article sur l'IA…",
        label_visibility="collapsed",
    )

    col_a, col_b, col_c = st.columns([1, 1, 1.35])
    with col_a:
        send = st.button(
            "Envoyer", type="primary", use_container_width=True, disabled=not prompt.strip()
        )
    with col_b:
        if st.button("Effacer", use_container_width=True):
            st.session_state.prompt_value = ""
            st.session_state.last_result = None
            st.session_state.last_prompt = None
            st.rerun()
    with col_c:
        st.caption("Appel bloquant `requests.post` (timeout sidebar) — historique à droite.")

    if send and prompt.strip():
        # Appel direct sans wrapper, pour rester fidèle au contrat
        t0 = time.perf_counter()
        with st.spinner("Envoi en cours…"):
            # clientA2A.send_prompt est synchrone ; on l'appelle tel quel
            result = clientA2A.send_prompt(prompt.strip())
        latency = time.perf_counter() - t0

        st.session_state.last_result = result
        st.session_state.last_prompt = prompt.strip()
        st.session_state.last_latency = latency
        st.session_state.prompt_value = prompt.strip()
        st.session_state.history.append(
            {
                "prompt": prompt.strip(),
                "result": result,
                "latency": latency,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ok": not result.startswith(("Error", "Request failed")),
            }
        )
        LOG.info("send_prompt lat=%.2fs ok=%s prompt=%r", latency, st.session_state.history[-1]["ok"], prompt[:60])
        st.rerun()

    # Résultat
    if st.session_state.last_result is not None:
        st.divider()
        res: str = st.session_state.last_result
        is_error = res.startswith(("Error", "Request failed"))
        is_empty_fallback = res == "No response from agent."

        st.subheader("Réponse")
        cols = st.columns([1, 1, 1])
        cols[0].metric("Latence", f"{st.session_state.last_latency:.2f}s" if st.session_state.last_latency else "—")
        cols[1].metric("Statut", "Erreur" if is_error else ("Vide" if is_empty_fallback else "OK"))
        cols[2].caption(f"Prompt : {st.session_state.last_prompt}")

        if is_error:
            st.error(res)
        elif is_empty_fallback:
            st.warning(res)
        else:
            # Heuristique outline : si ça ressemble à un outline, rend en liste
            if len(parse_outline(res)) >= 2:
                render_outline(res)
                with st.expander("Texte brut"):
                    st.code(res, language="markdown")
            else:
                st.markdown(f'<div class="outline-card"><p>{res}</p></div>', unsafe_allow_html=True)

        a1, a2, a3 = st.columns(3)
        with a1:
            st.download_button(
                "Télécharger .txt",
                data=res,
                file_name="reponse.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with a2:
            if st.button("Copier / Voir brut", use_container_width=True):
                st.code(res, language="text")
        with a3:
            st.caption(f"{len(res)} caractères")

    if st.session_state.last_result is None and not send:
        st.info("Astuce : choisis un exemple dans la sidebar ou saisis ton prompt ci-dessus.")

with right:
    st.subheader("Historique")
    hist = st.session_state.history
    if not hist:
        st.caption("Aucun envoi pour l'instant.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Vider", use_container_width=True):
                st.session_state.history = []
                st.session_state.last_result = None
                st.rerun()
        with c2:
            # Export CSV minimal
            import csv
            import io

            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["time", "prompt", "latency_s", "ok", "result"])
            for h in hist:
                w.writerow([h["time"], h["prompt"], f"{h['latency']:.3f}", h["ok"], h["result"][:500]])
            st.download_button(
                "Exporter CSV", data=buf.getvalue(), file_name="historique.csv", mime="text/csv", use_container_width=True
            )

        for h in reversed(hist):
            border = "1px solid #e2e8f0"
            with st.container(border=True):
                st.markdown(f"**{h['prompt'][:80]}**")
                st.caption(f"{h['time']} · {h['latency']:.2f}s · {'OK' if h['ok'] else 'Erreur'}")
                preview = h["result"][:200] + ("…" if len(h["result"]) > 200 else "")
                if h["ok"]:
                    st.markdown(preview)
                else:
                    st.error(preview) if preview.startswith(("Error", "Request failed")) else st.warning(preview)
                if st.button("Recharger", key=f"reload_{h['time']}_{h['prompt'][:10]}", use_container_width=True):
                    st.session_state.last_result = h["result"]
                    st.session_state.last_prompt = h["prompt"]
                    st.session_state.last_latency = h["latency"]
                    st.session_state.prompt_value = h["prompt"]
                    st.rerun()
