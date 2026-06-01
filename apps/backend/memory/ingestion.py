import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import FileRecord, MemoryChunk
from llm.openrouter import embed_text
from storage.service import StorageService


def _chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 2 <= max_chars:
            buf = f"{buf}\n\n{p}".strip() if buf else p
        else:
            if buf:
                chunks.append(buf)
            buf = p[:max_chars]
    if buf:
        chunks.append(buf)
    return chunks or [text[:max_chars]] if text else []


async def ingest_pdf_bytes(
    session: AsyncSession,
    workspace_id: str,
    filename: str,
    file_bytes: bytes,
    project_id: str | None = None,
) -> tuple[int, str]:
    import fitz  # PyMuPDF

    storage = StorageService()
    object_key = await storage.upload_file(workspace_id, file_bytes, filename)

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = "\n\n".join(page.get_text() for page in doc)
    doc.close()

    file_rec = FileRecord(
        workspace_id=workspace_id,
        project_id=project_id,
        filename=filename,
        file_type="pdf",
        storage_path=object_key,
        status="processing",
    )
    session.add(file_rec)
    await session.flush()

    pieces = _chunk_text(text)
    count = 0
    for piece in pieces:
        emb = await embed_text(piece)
        chunk = MemoryChunk(
            workspace_id=workspace_id,
            project_id=project_id,
            chunk_type="document_chunk",
            content=piece,
            source_file=filename,
            metadata_={},
        )
        session.add(chunk)
        await session.flush()
        if emb:
            from sqlalchemy import text

            vec = "[" + ",".join(str(x) for x in emb) + "]"
            await session.execute(
                text("UPDATE memory_chunks SET embedding = :e::vector WHERE id = :id"),
                {"e": vec, "id": chunk.id},
            )
        count += 1

    file_rec.chunk_count = count
    file_rec.status = "indexed"
    await session.flush()
    return count, object_key


async def create_note_chunk(
    session: AsyncSession,
    workspace_id: str,
    content: str,
    chunk_type: str = "strategy_note",
    project_id: str | None = None,
    entity_name: str | None = None,
) -> MemoryChunk:
    chunk = MemoryChunk(
        workspace_id=workspace_id,
        project_id=project_id,
        chunk_type=chunk_type,
        content=content,
        entity_name=entity_name,
        metadata_={},
    )
    session.add(chunk)
    await session.flush()
    emb = await embed_text(content)
    if emb:
        vec = "[" + ",".join(str(x) for x in emb) + "]"
        from sqlalchemy import text

        await session.execute(
            text("UPDATE memory_chunks SET embedding = :e::vector WHERE id = :id"),
            {"e": vec, "id": chunk.id},
        )
    return chunk
