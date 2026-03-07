import httpx

SEND_API_URL = "https://graph.facebook.com/v20.0/me/messages"


def send_text(recipient_id: str, text: str, access_token: str) -> None:
    response = httpx.post(
        SEND_API_URL,
        params={"access_token": access_token},
        json={"recipient": {"id": recipient_id}, "message": {"text": text}},
        timeout=10,
    )
    response.raise_for_status()
