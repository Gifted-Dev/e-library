from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from src.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.models import *

#|---- Creating Async Engine ---|
""" This creates an engine that helps with database connection"""
engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=True
)

#|---- Database Connection ----|
"""Creating initdb() to connect to the database
    and run sql statements"""
async def init_db():
    print("Running Init_db....")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("DB Initialized")
        
#|---- Create session factory ----|
async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


"""
This section sets up asynchronous database connectivity using SQLAlchemy and SQLModel:

1. An async engine is created with `create_async_engine`, 
using the database URL from the configuration. 
The `echo=True` flag enables SQL statement logging for debugging.


2. The `init_db` async function establishes a connection 
to the database and creates all tables defined in the SQLModel 
metadata. It uses `engine.begin()` for a transactional scope and `run_sync` to run 
the synchronous `create_all` method in an async context.


3. An async session factory (`async_session`) is created with `sessionmaker`. 
This factory produces `AsyncSession` objects bound to the engine, 
with `expire_on_commit=False` to keep objects accessible after committing.

Overall, this code prepares the app for async database operations: 
connecting, initializing tables, and managing sessions.
"""