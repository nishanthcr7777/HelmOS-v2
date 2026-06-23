"""Supabase SDK client — Storage only. Vectors/SQL use DATABASE_URL via SQLAlchemy."""

from functools import lru_cache

from supabase import Client, create_client

from config import get_settings


@lru_cache
def get_supabase_client() -> Client | None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_storage_bucket() -> str:
    return get_settings().storage_bucket
