import uuid

from db.supabase import get_storage_bucket, get_supabase_client


class StorageService:
    async def upload_file(self, workspace_id: str, file_bytes: bytes, filename: str) -> str:
        client = get_supabase_client()
        if client is None:
            return f"local/{workspace_id}/{uuid.uuid4()}/{filename}"

        object_key = f"{workspace_id}/{uuid.uuid4()}/{filename}"
        bucket = get_storage_bucket()
        client.storage.from_(bucket).upload(
            object_key,
            file_bytes,
            file_options={"content-type": "application/octet-stream", "upsert": "false"},
        )
        return object_key

    async def get_signed_url(self, object_key: str, expires_in: int = 3600) -> str:
        client = get_supabase_client()
        if client is None:
            return f"file://{object_key}"

        bucket = get_storage_bucket()
        result = client.storage.from_(bucket).create_signed_url(object_key, expires_in)
        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl") or ""
        return getattr(result, "signed_url", "") or ""

    async def delete_file(self, object_key: str) -> None:
        client = get_supabase_client()
        if client is None:
            return
        bucket = get_storage_bucket()
        client.storage.from_(bucket).remove([object_key])
