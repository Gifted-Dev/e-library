from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.auth.routes import auth_router
from src.books.routes import book_router
from src.admin.route import admin_router
from fastapi.responses import RedirectResponse

@asynccontextmanager
async def life_span(app: FastAPI):
    print("Server is starting up...")
    # In a production environment with Alembic, we don't want the app to create tables.
    # The `init_db()` 
    # This is the perfect place to initialize other resources like connection pools.
    yield
    print("Server is shutting down...")

version = "v1"

app = FastAPI(lifespan=life_span)

@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=['auth'])
app.include_router(book_router, prefix=f"/api/{version}/books", tags=['books'])
app.include_router(admin_router, prefix=f"/api/{version}/admin", tags=['admin'])
