from typing import Literal

from core.bot.Variables import Variables
from core.format import ReplaceVariables
from core.http import http


class Webhooks:
    async def send_webhook(
        self,
        webhookUrl: str,
        data: dict,
        feature: Literal["infractions", "promotions"],
        extra: dict | None = None,
    ):
        variables = None
        if feature == "infractions":
            variables = await Variables.infraction(
                extra.get("object"), extra.get("manager"), extra.get("guild")
            )
        if feature == "promotions":
            variables = await Variables.promotion(
                extra.get("object"), extra.get("manager"), extra.get("guild")
            )

        payload = ReplaceVariables(data, variables)

        await http.request(
            method="POST",
            url=webhookUrl,
            headers={"Content-Type": "application/json"},
            payload=payload,
        )
