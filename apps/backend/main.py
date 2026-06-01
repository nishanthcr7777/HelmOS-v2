from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import verify_api_key
from api.routes import (
    beliefs,
    board,
    chat,
    dashboard,
    decisions,
    entities,
    health,
    inbox,
    memory,
    research,
    workspaces,
)
from config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(title="HelmOS API", version="2.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router, dependencies=[Depends(verify_api_key)])
app.include_router(workspaces.router, dependencies=[Depends(verify_api_key)])
app.include_router(beliefs.router, dependencies=[Depends(verify_api_key)])
app.include_router(memory.router, dependencies=[Depends(verify_api_key)])
app.include_router(chat.router, dependencies=[Depends(verify_api_key)])
app.include_router(entities.router, dependencies=[Depends(verify_api_key)])
app.include_router(decisions.router, dependencies=[Depends(verify_api_key)])
app.include_router(inbox.router, dependencies=[Depends(verify_api_key)])
app.include_router(board.router, dependencies=[Depends(verify_api_key)])
app.include_router(research.router, dependencies=[Depends(verify_api_key)])
