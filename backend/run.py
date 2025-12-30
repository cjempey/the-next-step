"""Backend startup script."""

if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
