from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.router import router as chat_router
from app.auth.router import router as auth_router
from app.colors import configure_logging
from app.config import settings
from app.database import Base, engine
from app.ingestion.router import router as ingest_router
from app.models import user  # noqa: F401 (registers the model with Base)
from app.review.router import router as review_router

# Phase 14: leveled, timestamped logs instead of bare print()s — lets
# production turn down verbosity (INFO -> WARNING) without touching call
# sites. Still colored per module (by logger name) for terminal use, same as
# the old hand-rolled print()s, but that coloring now lives in one Formatter
# instead of being pasted into every call site.
configure_logging()

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
