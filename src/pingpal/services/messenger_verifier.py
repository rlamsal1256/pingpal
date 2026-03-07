import hashlib
import hmac


class MessengerVerificationError(Exception):
    """Raised when webhook requests fail integrity checks."""


def verify_challenge(mode: str | None, token: str | None, challenge: str | None, expected_token: str) -> str:
    if mode != "subscribe" or token != expected_token or challenge is None:
        raise MessengerVerificationError("Invalid verification challenge request")
    return challenge


def verify_signature(signature_header: str | None, request_body: bytes, app_secret: str) -> None:
    if not signature_header:
        raise MessengerVerificationError("Missing signature header")

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        msg=request_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature_header, expected):
        raise MessengerVerificationError("Invalid webhook signature")
