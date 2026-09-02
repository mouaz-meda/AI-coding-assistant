from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.models import user  # noqa: F401 (registers the model with Base)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok"}
