# AI Coding Assistant

A learning project: an AI assistant that understands code/projects and helps developers,
built with FastAPI, SQL, the OpenAI API, RAG, LangChain, and a vector DB.

See `CLAUDE.md` for development philosophy and roadmap.

## Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Then visit http://127.0.0.1:8000/health
