"""Composants Streamlit réutilisables pour le client outline.

Aucune logique métier ici : uniquement du rendu. La logique A2A vit dans
client.py, la config dans configs.py.
"""

from __future__ import annotations

import re

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --accent: #0f766e;
            --accent-hover: #0d5e57;
            --surface: #ffffff;
            --muted: #64748b;
            --border: #e2e8f0;
            --radius: 10px;
        }
        .block-container { padding-top: 1.6rem; max-width: 1100px; }
        header { visibility: hidden; }
        /* Carte résultat */
        .outline-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.1rem 1.2rem;
            margin-bottom: 0.8rem;
        }
        .outline-card h4 { margin: 0 0 0.4rem 0; font-size: 0.98rem; color: #0f172a; }
        .outline-card p, .outline-card li { color: #1e293b; line-height: 1.55; }
        /* Sidebar header */
        .sidebar-title { font-weight: 700; font-size: 1.05rem; color: #0f172a; margin-bottom: 0.2rem; }
        .sidebar-caption { color: var(--muted); font-size: 0.83rem; margin-bottom: 1rem; }
        /* Boutons */
        .stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--accent-hover);
            border-color: var(--accent-hover);
        }
        /* Status dots */
        .dot { display:inline-block; width:8px; height:8px; border-radius:999px; margin-right:6px; }
        .dot.ok { background:#16a34a; }
        .dot.off { background:#dc2626; }
        .dot.idle { background:#94a3b8; }
        /* Outline numbered list */
        .outline-list { counter-reset: sec; padding: 0; list-style: none; }
        .outline-list li {
            counter-increment: sec;
            display: flex; gap: 0.8rem;
            padding: 0.7rem 0.9rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            background: #f8fafc;
        }
        .outline-list li::before {
            content: counter(sec);
            flex: 0 0 28px; height: 28px;
            display: grid; place-items: center;
            background: #0f766e; color: white;
            border-radius: 999px; font-size: 0.82rem; font-weight: 700;
        }
        .meta { color: var(--muted); font-size: 0.83rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_outline(text: str) -> list[str]:
    """Découpe un outline brut en sections (tolérant aux formats)."""
    text = text.strip()
    if not text:
        return []
    # Supprime markdown titre
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Sépare par lignes numérotées / tirets
    candidates = re.split(r"\n+", text)
    sections: list[str] = []
    for line in candidates:
        line = line.strip()
        if not line:
            continue
        # 1. Titre  |  - Titre  |  I. Titre  |  • Titre
        line = re.sub(r"^(\d+[\.\)]|[-•–]|[IVX]+\.)\s*", "", line).strip()
        if len(line) < 3:
            continue
        # filtre les phrases d'intro / conclusion génériques trop longues
        sections.append(line)
        if len(sections) >= 8:
            break
    # Si une seule grosse ligne, tente split par phrases
    if len(sections) == 1 and len(sections[0]) > 180:
        parts = re.split(r"\s*;\s*|\s*\|\s*", sections[0])
        if len(parts) > 1:
            return [p.strip() for p in parts if p.strip()][:6]
    return sections[:6]


def render_outline(text: str) -> None:
    sections = parse_outline(text)
    if not sections:
        st.markdown(f'<div class="outline-card"><p>{text}</p></div>', unsafe_allow_html=True)
        return
    items = "".join(f"<li><span>{s}</span></li>" for s in sections)
    st.markdown(f'<ul class="outline-list">{items}</ul>', unsafe_allow_html=True)


def render_history(history: list[dict]) -> None:
    if not history:
        st.caption("Aucun outline généré pour l'instant.")
        return
    for idx, entry in enumerate(reversed(history), 1):
        with st.container(border=True):
            st.markdown(f"**{entry['topic']}**  \n<span class='meta'>{entry['time']}</span>", unsafe_allow_html=True)
            st.caption(entry["text"][:220] + ("…" if len(entry["text"]) > 220 else ""))
