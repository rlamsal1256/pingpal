import httpx
import respx

from pingpal.services.messenger_client import SEND_API_URL, send_text


@respx.mock
def test_send_text_calls_graph_api() -> None:
    route = respx.post(SEND_API_URL).mock(return_value=httpx.Response(200, json={"message_id": "mid.123"}))

    send_text(recipient_id="user-1", text="hello", access_token="tok")

    assert route.called
    request = route.calls.last.request
    assert b'"hello"' in request.content
    assert b'"user-1"' in request.content
    assert b"tok" in request.url.query


@respx.mock
def test_send_text_raises_on_error() -> None:
    respx.post(SEND_API_URL).mock(return_value=httpx.Response(400, json={"error": "bad token"}))

    try:
        send_text(recipient_id="user-1", text="hello", access_token="bad")
    except httpx.HTTPStatusError:
        pass
    else:
        raise AssertionError("Expected HTTPStatusError")
