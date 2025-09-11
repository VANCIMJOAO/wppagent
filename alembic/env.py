import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from app.models.database import Base
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# H003 FIX - Override URL with DATABASE_URL environment variable
# This ensures production environments use PostgreSQL instead of SQLite
import os
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Escape % characters for configparser
    escaped_url = database_url.replace('%', '%%')
    config.set_main_option("sqlalchemy.url", escaped_url)
    print(f"H003 - Using DATABASE_URL from environment: {database_url[:20]}...")
else:
    # Fallback to settings.database_url if available
    if hasattr(settings, 'database_url') and settings.database_url:
        escaped_url = settings.database_url.replace('%', '%%')
        config.set_main_option("sqlalchemy.url", escaped_url)
        print(f"H003 - Using settings.database_url: {settings.database_url[:20]}...")
    else:
        print("H003 - Using fallback SQLite from alembic.ini (development mode)")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy.ext.asyncio import create_async_engine
    import os
    
    # H003 FIX - Improved database URL resolution
    # Priority: 1. DATABASE_URL env var, 2. alembic.ini, 3. fallback
    database_url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    
    if not database_url:
        database_url = "sqlite+aiosqlite:///./whatsapp_agent.db"
        print("H003 - WARNING: No DATABASE_URL found, using SQLite fallback")
    
    # Convert to async driver if necessary
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        print("H003 - Converted PostgreSQL URL to async driver")
    elif database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        print("H003 - Converted SQLite URL to async driver")
    
    print(f"H003 - Connecting to: {database_url.split('@')[-1] if '@' in database_url else database_url[:30]}...")
    
    connectable = create_async_engine(database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
