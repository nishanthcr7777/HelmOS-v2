import asyncio
import sys

from httpx import AsyncClient


async def main() -> int:
    async with AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:8000/chat/stream",
            headers={
                "Authorization": "Bearer dev-key",
                "Content-Type": "application/json",
            },
            json={
                "message": "What is our ICP for Clawback Labs?",
                "workspace_id": "clawback-labs",
            },
        )
        print("status", response.status_code)
        body = response.text
        if response.status_code != 200:
            print(body[:500])
            return 1
        if "OPENROUTER_API_KEY" in body or "running without" in body:
            print("FAIL: fallback message")
            return 1
        if "token" not in body:
            print("FAIL: no SSE tokens")
            print(body[:500])
            return 1
        print("PASS: OpenRouter SSE streaming")
        print(body[:600])
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
