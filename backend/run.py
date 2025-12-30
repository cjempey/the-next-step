"""Backend startup script."""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    from app.config import settings

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
