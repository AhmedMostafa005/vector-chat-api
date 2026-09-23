# Vector Chat API

A FastAPI-based service that provides semantic search and chat capabilities using vector embeddings and pgvector for similarity search.

## Architecture

- **Framework**: FastAPI (Python) with async support
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **Embeddings**: OpenAI text-embedding-3-small model
- **Chat**: Anthropic Claude API
- **Deployment**: Railway

## Features

- **GET /users**: List all users
- **POST /users/{user_id}/text**: Store text embeddings for a user
- **POST /users/{user_id}/chat**: Chat with context retrieved from stored embeddings

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- OpenAI API key
- Anthropic API key

### Local Development

1. Clone the repository and navigate to the project directory:
```bash
cd vector-chat-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

4. Initialize the database schema:
```bash
python init_db.py
```

This will create the required tables and enable the pgvector extension.

5. Create a test user:
```bash
python create_user.py "Test User"
```

This will output a user ID that you can use for testing.

6. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

7. Test the API:
```bash
python test_api.py
```

This will run through the basic functionality using the first user in the database.

## API Endpoints

### GET /users
List all users in the system.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "user name",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### POST /users/{user_id}/text
Store text embeddings for a specific user.

**Request Body:**
```json
{
  "text": "Your text content here"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Text embedded and stored successfully"
}
```

### POST /users/{user_id}/chat
Chat with context retrieved from stored embeddings.

**Request Body:**
```json
{
  "message": "Your question here"
}
```

**Response:**
```json
{
  "response": "AI response based on context",
  "context_used": ["relevant context 1", "relevant context 2"]
}
```

## Railway Deployment

1. Push your code to a GitHub repository
2. Create a new project in Railway
3. Select "Deploy from GitHub repo"
4. Add a Postgres plugin from Railway's marketplace
5. Set environment variables in Railway:
   - `DATABASE_URL` (auto-set by Railway)
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
6. Railway will auto-build and deploy on every push

### Database Setup on Railway

After deployment, you'll need to initialize the database schema. You can do this by:

1. Using Railway's query console to run the SQL commands in `schema.sql`
2. Or temporarily adding a startup script to run the initialization

The schema initialization requires the pgvector extension, which must be enabled on your Railway Postgres instance.

## Helper Scripts

The project includes several helper scripts for development:

- `init_db.py`: Initialize the database schema (tables, indexes, pgvector extension)
- `create_user.py`: Create a new user in the database (optional name parameter)
- `test_api.py`: Test the API endpoints with sample data

Run these scripts after setting up your environment variables.

## Database Schema

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON vectors USING ivfflat (embedding vector_cosine_ops);
```

## How It Works

1. **Text Storage**: When you POST text to `/users/{user_id}/text`, the text is sent to OpenAI's embedding API to generate a 1536-dimensional vector, which is stored in PostgreSQL.

2. **Chat**: When you POST a message to `/users/{user_id}/chat`:
   - The message is embedded using the same model
   - A similarity search is performed using pgvector's cosine distance operator (`<=>`)
   - The top 5 most similar text chunks are retrieved as context
   - The context and question are sent to Claude for a response
   - The response is returned along with the context used

## Development Notes

- Embeddings are generated synchronously (simpler implementation)
- Chat responses are returned in one shot (not streaming)
- The system uses cosine similarity for vector search
- Each user's vectors are isolated for privacy

## Troubleshooting

### Database Connection Issues
- Ensure your `DATABASE_URL` is correctly formatted
- Verify PostgreSQL is running and accessible
- Check that the pgvector extension is installed

### API Key Issues
- Verify your OpenAI and Anthropic API keys are valid
- Ensure you have sufficient credits/API quota

### Performance
- For large datasets, consider adjusting the IVFFlat index parameters
- The current implementation returns top 5 context chunks

## License

MIT
