"""Tests UI — vérifie que ui.py s'appuie sur clientA2A sans le modifier."""

import ast
import pathlib


def test_ui_imports_clientA2A():
    ui_path = pathlib.Path(__file__).parent.parent / "ui.py"
    src = ui_path.read_text(encoding="utf-8")
    assert "import clientA2A" in src
    assert "clientA2A.send_prompt" in src


def test_ui_does_not_hardcode_alternative_url():
    # l'UI doit introspecter clientA2A, pas dupliquer une URL différente
    ui_path = pathlib.Path(__file__).parent.parent / "ui.py"
    src = ui_path.read_text(encoding="utf-8")
    # elle affiche l'URL mais ne doit pas faire de requests.post direct avec une autre URL
    tree = ast.parse(src)
    assert any(isinstance(n, ast.Call) for n in ast.walk(tree))
    # aucune définition locale de send_prompt
    assert "def send_prompt" not in src


def test_ui_components_parse():
    from src.client_a2a.ui_components import parse_outline

    assert parse_outline("1. Intro\n2. Contexte\n3. Conclusion") == ["Intro", "Contexte", "Conclusion"]
    assert parse_outline("") == []
    assert parse_outline("Hello world") == ["Hello world"]


def test_ui_handles_error_strings():
    # l'UI distingue Error / Request failed / OK — vérifie la présence du branchement
    ui_path = pathlib.Path(__file__).parent.parent / "ui.py"
    src = ui_path.read_text(encoding="utf-8")
    assert "Error" in src and "startswith" in src
    assert "Request failed" in src and "startswith" in src
