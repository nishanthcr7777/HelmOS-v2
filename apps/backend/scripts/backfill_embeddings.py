"""Backfill NULL embeddings on memory_chunks. Run: python scripts/backfill_embeddings.py"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from llm.openrouter import embed_text


async def main() -> int:
    settings = get_settings()
    if not settings.openrouter_api_key:
        print("OPENROUTER_API_KEY not set — cannot embed")
        return 1

    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, connect_args={"statement_cache_size": 0})
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    backfilled = 0
    skipped = 0
    errors = 0

    async with Session() as session:
        rows = (
            await session.execute(
                text("SELECT id, content FROM memory_chunks WHERE embedding IS NULL")
            )
        ).mappings().all()

        print(f"Found {len(rows)} chunks without embeddings")

        for row in rows:
            chunk_id = row["id"]
            content = row["content"] or ""
            if not content.strip():
                skipped += 1
                continue
            try:
                emb = await embed_text(content)
                if not emb:
                    skipped += 1
                    continue
                vec = "[" + ",".join(str(x) for x in emb) + "]"
                await session.execute(
                    text("UPDATE memory_chunks SET embedding = CAST(:e AS vector) WHERE id = :id"),
                    {"e": vec, "id": chunk_id},
                )
                backfilled += 1
                if backfilled % 10 == 0:
                    await session.commit()
                    print(f"  backfilled {backfilled}...")
            except Exception as exc:
                errors += 1
                print(f"  error on {chunk_id}: {exc}")

        await session.commit()

    await engine.dispose()
    print(f"Done: backfilled={backfilled} skipped={skipped} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
