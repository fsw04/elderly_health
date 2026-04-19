from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.api import api_router
from app.core.config import settings
from app.db.session import engine
from app.models.all import Base
from contextlib import asynccontextmanager
from app.ingest.mqtt import setup_mqtt

async def ensure_schema_compatibility(conn):
    # Lightweight migration for existing SQLite databases.
    result = await conn.execute(text("PRAGMA table_info(users)"))
    existing_columns = {row[1] for row in result.fetchall()}
    if "current_address" not in existing_columns:
        await conn.execute(text("ALTER TABLE users ADD COLUMN current_address VARCHAR"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (only for MVP without migrations, or use alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_schema_compatibility(conn)
    
    # Initialize MQTT
    setup_mqtt()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
