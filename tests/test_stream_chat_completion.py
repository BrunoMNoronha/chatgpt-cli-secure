import json
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, Iterator, List

import requests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from gpt_cli import Config, stream_chat_completion


class FakeResponse:
    def __init__(self, lines: List[str]) -> None:
        self.status_code: int = 200
        self._lines: List[str] = lines
        self.text: str = ""

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def iter_lines(self) -> Iterator[bytes]:
        for line in self._lines:
            yield line.encode("utf-8")


def old_stream_chat_completion(
    api_key: str, payload: Dict[str, Any], timeout: float
) -> str:
    headers: Dict[str, str] = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    response_text: str = ""
    with requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        stream=True,
        timeout=timeout,
    ) as r:  # type: ignore[assignment]
        for line in r.iter_lines():
            if not line:
                continue
            decoded: str = line.decode("utf-8")
            if decoded.startswith("data:"):
                content: str = decoded[len("data:") :].strip()
                if content == "[DONE]":
                    break
                event = json.loads(content)
                delta = event.get("choices", [{}])[0].get("delta", {})
                c = delta.get("content")
                if c:
                    print(c, end="", flush=True)
                    response_text += c
        print()
    return response_text


def test_stream_chat_completion_equivalence(monkeypatch) -> None:
    lines: List[str] = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        'data: [DONE]',
    ]

    def fake_post_old(*args: Any, **kwargs: Any) -> FakeResponse:
        assert "data" in kwargs
        return FakeResponse(lines)

    def fake_post_new(*args: Any, **kwargs: Any) -> FakeResponse:
        assert "json" in kwargs
        return FakeResponse(lines)

    monkeypatch.setattr(requests, "post", fake_post_old)
    with redirect_stdout(StringIO()) as old_out:
        old_result: str = old_stream_chat_completion("key", {}, 0.0)
    old_print: str = old_out.getvalue()

    monkeypatch.setattr(requests, "post", fake_post_new)
    with redirect_stdout(StringIO()) as new_out:
        new_result: str = stream_chat_completion(
            "key", [], Config(model="m", temperature=0.0), 0.0
        )
    new_print: str = new_out.getvalue()

    assert old_result == new_result
    assert old_print == new_print
