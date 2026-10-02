from typing import Literal

import aiohttp


class http:

    async def request(
        self,
        url: str,
        method: Literal["GET", "PUSH"],
        payload: dict | None = None,
        headers: dict | None = None,
    ):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method, url=url, json=payload, headers=headers
            ) as response:
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
