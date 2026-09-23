from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.router import router as chat_router
from app.auth.router import router as auth_router
from app.config import settings
from app.database import Base, engine
from app.ingestion.router import router as ingest_router
from app.models import user  # noqa: F401 (registers the model with Base)
from app.review.router import router as review_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(review_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.port, reload=True)
