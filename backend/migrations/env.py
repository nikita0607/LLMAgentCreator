import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db import Base

from app.models.user import User
from app.models.session_message import SessionMessage
from app.models.agent import Agent
from app.models.session import Session
from app.models.knowledge_base import KnowledgeEmbedding, KnowledgeNode

# эта конфигурация — из alembic.ini
config = context.config
# переопределим URL на тот, что в .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Логгинг
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Запуск миграций в онлайн-режиме"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()