#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize database with new schema."""

import asyncio
import sys
sys.path.insert(0, 'src')

from agent_builder.core.database import init_db, async_session_factory
from agent_builder.db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine
from agent_builder.core.config import settings

async def main():
    print("Initializing database...")

    # Create all tables
    await init_db()

    print("Database initialized successfully!")

    # Verify tables created
    async with async_session_factory() as db:
        from sqlalchemy import text
        result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"\nCreated tables: {len(tables)}")
        for table in sorted(tables):
            print(f"  - {table}")

if __name__ == "__main__":
    asyncio.run(main())
