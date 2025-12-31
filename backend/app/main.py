"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import tasks, values, reviews, suggestions
from app.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="The Next Step API",
        description="Task suggestion service for neurodivergent individuals",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Include routers
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(values.router, prefix="/api/values", tags=["values"])
    app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
    app.include_router(
        suggestions.router, prefix="/api/suggestions", tags=["suggestions"]
    )

    return app


app = create_app()
