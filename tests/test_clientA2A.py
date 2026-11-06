"""Tests pour clientA2A.py — sans le modifier, en mockant requests.

Couvre exactement son contrat :
- URL dure = https://server-a2a-routing-agent.onrender.com/message
- payload {"message": prompt}
- 200 -> response.json()["response"] sinon "No response from agent."
- !200 -> "Error {code}: {text}"
- exception -> "Request failed: {e}"
"""

from unittest.mock import MagicMock, patch

import clientA2A

EXPECTED_URL = "https://server-a2a-routing-agent.onrender.com/message"


def _mock_resp(status_code=200, json_data=None, text=""):
    m = MagicMock()
    m.status_code = status_code
    m.text = text
    m.json.return_value = json_data if json_data is not None else {}
    return m


def test_send_prompt_success_with_response():
    mock = _mock_resp(200, {"response": "hello world"})
    with patch("clientA2A.requests.post", return_value=mock) as post:
        result = clientA2A.send_prompt("bonjour")

    assert result == "hello world"
    post.assert_called_once_with(EXPECTED_URL, json={"message": "bonjour"})


def test_send_prompt_success_fallback_no_response_key():
    mock = _mock_resp(200, {"other": "x"})
    with patch("clientA2A.requests.post", return_value=mock):
        result = clientA2A.send_prompt("test")

    assert result == "No response from agent."


def test_send_prompt_success_none_response_value():
    # json().get("response", "No response...") -> si clé présente mais None, renvoie None
    mock = _mock_resp(200, {"response": None})
    with patch("clientA2A.requests.post", return_value=mock):
        result = clientA2A.send_prompt("test")

    assert result is None  # comportement actuel du code


def test_send_prompt_error_status():
    mock = _mock_resp(500, {}, text="Internal Server Error")
    with patch("clientA2A.requests.post", return_value=mock):
        result = clientA2A.send_prompt("hello")

    assert result == "Error 500: Internal Server Error"


def test_send_prompt_error_404():
    mock = _mock_resp(404, {}, text="Not Found")
    with patch("clientA2A.requests.post", return_value=mock):
        result = clientA2A.send_prompt("hello")

    assert result == "Error 404: Not Found"


def test_send_prompt_request_exception():
    with patch("clientA2A.requests.post", side_effect=Exception("timeout")):
        result = clientA2A.send_prompt("hello")

    assert result == "Request failed: timeout"


def test_send_prompt_connection_error():
    import requests as req

    with patch("clientA2A.requests.post", side_effect=req.exceptions.ConnectionError("dns")):
        result = clientA2A.send_prompt("hello")

    assert result.startswith("Request failed:")


def test_send_prompt_payload_exact():
    mock = _mock_resp(200, {"response": "ok"})
    with patch("clientA2A.requests.post", return_value=mock) as post:
        clientA2A.send_prompt("mon message")

    # vérifie que le payload est exactement {"message": prompt}
    _, kwargs = post.call_args
    assert kwargs["json"] == {"message": "mon message"}
    assert post.call_args[0][0] == EXPECTED_URL


def test_send_prompt_url_hardcoded():
    # s'assure que clientA2A.py n'a pas été modifié pour utiliser HOST/PORT
    import inspect

    src = inspect.getsource(clientA2A.send_prompt)
    assert EXPECTED_URL in src
