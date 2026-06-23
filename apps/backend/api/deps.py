from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from db.session import get_db

bearer = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> None:
    settings = get_settings()
    if not settings.helmos_api_key:
        return
    if credentials is None or credentials.credentials != settings.helmos_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


DbSession = Annotated[AsyncSession, Depends(get_db)]
Auth = Annotated[None, Depends(verify_api_key)]
