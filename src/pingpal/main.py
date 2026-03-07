import logging

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from pingpal.api.webhook import handle_challenge, handle_webhook
from pingpal.config import settings
from pingpal.services.messenger_client import send_text

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/webhook")
async def webhook_challenge(request: Request) -> Response:
    result = handle_challenge(dict(request.query_params))
    if isinstance(result.body, str):
        return PlainTextResponse(result.body, status_code=result.status_code)
    return JSONResponse(result.body, status_code=result.status_code)


@app.post("/webhook")
async def webhook_event(request: Request) -> JSONResponse:
    raw_body = await request.body()
    payload = await request.json()
    signature = request.headers.get("X-Hub-Signature-256")
    result = handle_webhook(payload=payload, raw_body=raw_body, signature_header=signature)

    if result.replies:
        if settings.messenger_page_access_token:
            for recipient_id, reply_text in result.replies:
                try:
                    send_text(recipient_id, reply_text, settings.messenger_page_access_token)
                except Exception:
                    logger.exception("Failed to send reply to %s", recipient_id)
        else:
            logger.warning("MESSENGER_PAGE_ACCESS_TOKEN not set; skipping %d reply(s)", len(result.replies))

    return JSONResponse(result.body, status_code=result.status_code)
