from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.api import auth, agents, sessions, webhooks, knowledge_base
from app.core.run_migrations import run_migrations

app = FastAPI(title="LLM Agents")

# Run migrations on startup
@app.on_event("startup")
async def startup_event():
    # Run migrations in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_migrations)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # фронт
    allow_credentials=True,
    allow_methods=["*"],  # разрешить все методы (включая OPTIONS)
    allow_headers=["*"],
)

# Роуты с префиксом /api
app.include_router(auth.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(knowledge_base.router, prefix="/api")