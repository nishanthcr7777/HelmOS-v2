import asyncio
import sys

from httpx import AsyncClient


async def main() -> int:
    async with AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "http://localhost:8000/board/sessions",
            headers={
                "Authorization": "Bearer dev-key",
                "Content-Type": "application/json",
            },
            json={
                "question": "Is Acme Corp a good Clawback target?",
                "workspace_id": "clawback-labs",
            },
        )
        print("status", response.status_code)
        if response.status_code != 201:
            print(response.text[:800])
            return 1
        data = response.json()
        session_id = data.get("id")
        status = data.get("status")
        agents = len(data.get("agent_outputs") or [])
        synthesis = bool(data.get("synthesis"))
        print("session_id", session_id)
        print("status", status, "agents", agents, "synthesis", synthesis)
        if status != "complete" or agents < 5 or not synthesis:
            print("FAIL: incomplete board session")
            return 1
        print("PASS: board session complete")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
