-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create vectors table
CREATE TABLE IF NOT EXISTS vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS vectors_embedding_idx 
ON vectors USING ivfflat (embedding vector_cosine_ops);
