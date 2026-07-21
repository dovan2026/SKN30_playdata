from __future__ import annotations

from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from app.core.config import Settings
from app.services.slack_service import SlackHandlers


def create_slack_app(
    settings: Settings,
    handlers: SlackHandlers,
    *,
    client: AsyncWebClient | None = None,
) -> AsyncApp:
    if not settings.slack_configured:
        raise ValueError("SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET are required")
    slack_client = client or AsyncWebClient(
        token=settings.slack_bot_token.get_secret_value()  # type: ignore[union-attr]
    )
    app = AsyncApp(
        client=slack_client,
        signing_secret=settings.slack_signing_secret.get_secret_value(),  # type: ignore[union-attr]
    )


    # Slack의 /econ 명령과 채널 메시지 이벤트를 감지해 각각 지정된 핸들러로 전달




    return app

