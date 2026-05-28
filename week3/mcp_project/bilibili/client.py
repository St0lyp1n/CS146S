from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bilibili")
USER_AGENT = "bilibili-app/1.0"


async def make_user_card_request(
    url: str,
    *,
    mid: int,
    photo: bool = True,
) -> dict[str, Any] | None:
    """向哔哩哔哩用户名片 API 发起请求并进行适当的错误处理。"""
    headers = {"User-Agent": USER_AGENT, "Referer": "https://www.bilibili.com"}
    params = {"mid": mid, "photo": photo}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, params=params, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            body = response.json()
            if body.get("code") != 0:
                return None
            return body["data"]
        except Exception:
            return None
