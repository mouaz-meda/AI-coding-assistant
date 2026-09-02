from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.config import settings
from app.database import Base, engine
from app.models import user  # noqa: F401 (registers the model with Base)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
