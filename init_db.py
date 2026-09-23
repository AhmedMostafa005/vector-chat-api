import asyncio
from sqlalchemy import text
from database import get_db_session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def init_database():
    """Initialize the database schema with pgvector extension and required tables."""
    async_session_maker = get_db_session(DATABASE_URL)
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("Enabled pgvector extension")

            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            print("Created users table")

            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vectors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """))
            print("Created vectors table")

            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS vectors_embedding_idx
                ON vectors USING ivfflat (embedding vector_cosine_ops)
            """))
            print("Created vector similarity index")

        await session.commit()
        print("Database schema initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
