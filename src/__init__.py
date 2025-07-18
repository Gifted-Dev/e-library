from fastapi import FastAPI
from src.db import models
from src.db.models import Book, User
from src.db.main import init_db
from contextlib import asynccontextmanager
from src.auth.routes import auth_router
from src.books.routes import book_router

@asynccontextmanager
async def life_span(app: FastAPI):
    print("server is starting....")
    try:
        # await init_db()
        print("Database Initialization complete.")
    except Exception as e:
        print(f"Error Initalizing database: {e}")
    yield
    print("Server has been stopped....")

version = "v1"

app = FastAPI()


app.include_router(auth_router, prefix="/api/{version}/auth", tags=['auth'])
app.include_router(book_router, prefix="/api/{version}/books", tags=['books'])
