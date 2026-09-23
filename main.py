from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from database import get_db_session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = 1536


if not all([DATABASE_URL, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables: DATABASE_URL, GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


async def get_db():
    async_session_maker = get_db_session(DATABASE_URL)
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    async_session_maker = get_db_session(DATABASE_URL)
    async with async_session_maker() as session:
        try:
            async with session.begin():
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as e:
            print(f"Warning: Could not enable pgvector extension: {e}")
    yield


app = FastAPI(title="Vector Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserResponse(BaseModel):
    id: str
    name: Optional[str]
    created_at: Optional[str]


class TextRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    context_used: List[str]


async def embed_text(content: str) -> str:
    """Returns a pgvector-literal string like '[0.01,-0.02,...]'."""
    try:
        result = await gemini_client.aio.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=content,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        values = result.embeddings[0].values
        return "[" + ",".join(str(v) for v in values) + "]"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")


@app.get("/users", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT id, name, created_at FROM users ORDER BY created_at DESC"))
    users = result.fetchall()
    return [
        UserResponse(
            id=str(user[0]),
            name=user[1],
            created_at=user[2].isoformat() if user[2] else None
        )
        for user in users
    ]


@app.post("/users/{user_id}/text")
async def store_text(user_id: str, request: TextRequest, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id})
    if not user_result.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    embedding_literal = await embed_text(request.text)

    await db.execute(
        text("""
            INSERT INTO vectors (user_id, content, embedding)
            VALUES (:user_id, :content, CAST(:embedding AS vector))
        """),
        {"user_id": user_id, "content": request.text, "embedding": embedding_literal}
    )
    await db.commit()

    return {"status": "success", "message": "Text embedded and stored successfully"}


@app.post("/users/{user_id}/chat", response_model=ChatResponse)
async def chat(user_id: str, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id})
    if not user_result.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    query_embedding_literal = await embed_text(request.message)

    similarity_query = text("""
        SELECT content, embedding <=> CAST(:embedding AS vector) as distance
        FROM vectors
        WHERE user_id = :user_id
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT 5
    """)

    result = await db.execute(
        similarity_query,
        {"embedding": query_embedding_literal, "user_id": user_id}
    )
    similar_vectors = result.fetchall()

    if not similar_vectors:
        context = "No relevant context found."
        context_used = []
    else:
        context_parts = [row[0] for row in similar_vectors]
        context = "\n\n".join([f"Context {i+1}: {t}" for i, t in enumerate(context_parts)])
        context_used = context_parts

    prompt = f"""You are a helpful assistant. Use the following context to answer the user's question. If the context doesn't contain relevant information, say so.

Context:
{context}

User's question: {request.message}

Please provide a helpful response based on the context above."""

    try:
        response = await gemini_client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        response_text = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

    return ChatResponse(
        response=response_text,
        context_used=context_used
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
