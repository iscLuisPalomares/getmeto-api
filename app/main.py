from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)


@app.get("/", tags=["service"])
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health", tags=["service"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
