import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import models  # noqa: F401  (registers tables)
from database import Base, engine
from logging_config import setup_logging
from v1.admins.router import router as admins_router
from v1.users.router import router as users_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Application started (database tables ready)")
    yield
    logger.info("Application shutting down")


app = FastAPI(title="Voting System - Auth API", version="1.0.0", lifespan=lifespan)
app.include_router(users_router)
app.include_router(admins_router)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        # don't restart when the app writes its own logs or database
        reload_excludes=["logs/*", "*.log", "*.db"],
    )
