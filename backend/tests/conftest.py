"""Pytest configuration and fixtures."""

import asyncio

# Test database URL (use PostgreSQL for tests to support ARRAY types)
# Can be overridden with TEST_DATABASE_URL environment variable
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.db import get_session
from app.main import app

# Import all models to ensure they're registered with SQLModel
from app.models import Clip, Transcript, User, Video  # noqa: F401

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/videodb_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,  # Verify connections before using
    )

    # Create tables - use begin() for DDL operations (auto-commits)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    # Force a new connection to verify tables exist
    async with engine.connect() as check_conn:
        await check_conn.execute(text("SELECT 1 FROM videos LIMIT 1"))
        await check_conn.close()

    # Create async session factory
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create session
    async with async_session_maker() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    # Drop tables after test
    async with engine.connect() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.commit()

    await engine.dispose()


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator:
    """Create a test client with database session override."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
