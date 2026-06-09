import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.deps import DbSession
from beliefs.service import BeliefService
from llm.openrouter import stream_chat_completion
from memory.retrieval import MemoryService

router = APIRouter(prefix="/chat", tags=["chat"])

DEFAULT_WORKSPACE = "clawback-labs"


class ChatRequest(BaseModel):
    message: str
    workspace_id: str = DEFAULT_WORKSPACE


@router.post("/stream")
async def chat_stream(body: ChatRequest, db: DbSession):
    beliefs_svc = BeliefService(db)
    beliefs_block = await beliefs_svc.pack_for_prompt(body.workspace_id)

    memory = MemoryService(db)
    memory_result = await memory.search(body.message, body.workspace_id, limit=8)
    chunks = memory_result.chunks
    memory_block = "\n".join(f"- [{c.chunk_type}] {c.content[:600]}" for c in chunks)
    evidence = [
        {
            "source": "memory_chunk",
            "snippet": c.content[:200],
            "chunk_id": c.id,
            "url": c.source_url,
        }
        for c in chunks[:5]
    ]

    system = f"""You are HelmOS, a founder intelligence assistant. Ground answers in context.
Be concise. Cite memory when relevant. Respect strategic beliefs as doctrine.

{beliefs_block}

## Retrieved memory
{memory_block or "No chunks retrieved."}
"""

    async def event_stream():
        full = ""
        async for token in stream_chat_completion(system, body.message):
            full += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        confidence = 0.72 if chunks else 0.45
        yield f"data: {json.dumps({'type': 'done', 'confidence': confidence, 'tag': 'plain', 'evidence': evidence})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
