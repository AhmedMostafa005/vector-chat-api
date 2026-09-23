import asyncio
import sys
from sqlalchemy import text
from database import get_db_session
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def create_user(name: str = None):
    async_session_maker = get_db_session(DATABASE_URL)
    async with async_session_maker() as session:
        user_id = str(uuid.uuid4())
        await session.execute(
            text("INSERT INTO users (id, name) VALUES (:id, :name)"),
            {"id": user_id, "name": name}
        )
        await session.commit()
        print(f"Created user with ID: {user_id}")
        return user_id


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(create_user(name))

