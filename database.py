from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

_session_maker = None


def get_db_session(database_url: str):
    """Returns a cached async_sessionmaker, creating the engine once."""
    global _session_maker
    if _session_maker is None:
        engine = create_async_engine(database_url, echo=False)
        _session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _session_maker
