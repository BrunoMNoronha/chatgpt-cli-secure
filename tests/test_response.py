from typing import Any

def test_response_without_message_key() -> None:
    data: dict[str, list[dict[str, Any]]] = {"choices": [{}]}
    response_text: str = data["choices"][0].get("message", {}).get("content", "")
    assert response_text == ""
