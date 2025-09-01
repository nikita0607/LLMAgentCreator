from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, agents, sessions, webhooks, knowledge_base

app = FastAPI(title="LLM Agents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # фронт
    allow_credentials=True,
    allow_methods=["*"],  # разрешить все методы (включая OPTIONS)
    allow_headers=["*"],
)

# Роуты
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(sessions.router)
app.include_router(webhooks.router)
app.include_router(knowledge_base.router)