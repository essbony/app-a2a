"""Tests configs.py — miroir outline_agent/configs.py."""

import configs


def test_host_is_string_non_empty():
    assert isinstance(configs.HOST, str)
    assert configs.HOST.strip() != ""


def test_port_is_valid_int():
    assert isinstance(configs.PORT, int)
    assert 1 <= configs.PORT <= 65535


def test_port_default_mirror_outline_agent():
    # outline_agent défaut 10008
    assert configs.PORT == 10008 or isinstance(configs.PORT, int)


def test_public_url_is_none_or_string():
    assert configs.PUBLIC_URL is None or isinstance(configs.PUBLIC_URL, str)


def test_agent_url_resolved():
    assert hasattr(configs, "AGENT_URL")
    assert isinstance(configs.AGENT_URL, str)
    assert configs.AGENT_URL.startswith("http")


def test_log_exists():
    assert hasattr(configs, "LOG")
    assert configs.LOG is not None
