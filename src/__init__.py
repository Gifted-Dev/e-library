from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.auth.routes import auth_router
from src.books.routes import book_router
from src.admin.route import admin_router
from fastapi.responses import RedirectResponse
from src.config import Config
from src.core.error_handlers import EXCEPTION_HANDLERS
from src.core.redis import startup_redis, shutdown_redis
from src.db.main import init_db


version = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("🚀 Starting E-Library application...")

    # Initialize database tables
    print("📊 Initializing database...")
    await init_db()

    # Initialize Redis connection
    print("🔴 Initializing Redis...")
    await startup_redis()

    print("✅ Application startup complete!")
    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await shutdown_redis()
    print("✅ Application shutdown complete!")


app = FastAPI(
    title="E-Library API",
    description="A comprehensive e-library management system",
    version="1.0.0",
    lifespan=lifespan
)

# Add exception handlers
for exception_type, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_type, handler)

# --- CORS Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=[Config.CLIENT_DOMAIN] if Config.ENVIRONMENT == "development" else [Config.CLIENT_DOMAIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Health check endpoint for production monitoring.
    """
    from src.core.redis import redis_service

    redis_status = await redis_service.health_check()
    redis_info = await redis_service.get_redis_info()

    return {
        "status": "healthy" if redis_status else "degraded",
        "services": {
            "redis": {
                "status": "up" if redis_status else "down",
                "info": redis_info
            }
        }
    }

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=['auth'])
app.include_router(book_router, prefix=f"/api/{version}/books", tags=['books'])
app.include_router(admin_router, prefix=f"/api/{version}/admin", tags=['admin'])
