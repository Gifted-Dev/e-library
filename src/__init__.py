from fastapi import FastAPI
from src.db import models
from src.db.models import Book, User
from src.db.main import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def life_span(app: FastAPI):
    print("server is starting....")
    try:
        await init_db()
        print("Database Initialization complete.")
    except Exception as e:
        print(f"Error Initalizing database: {e}")
    yield
    print("Server has been stopped....")

app = FastAPI(lifespan=life_span)

