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

To run on a different port, either pass `--port` to the command above, or set `PORT` in `.env`
and run `python -m app.main` instead (reads the port from config, but no `--reload` autodetection
outside uvicorn's CLI).

Then visit http://127.0.0.1:8000/health (or your configured port).

To let `POST /ingest/path` read a folder on the server, set `INGEST_ROOT` in `.env` (paths are
resolved inside that folder; leave it empty to disable). Browser uploads (`POST /ingest/upload`)
need no setup.

## Using a local model instead of OpenAI

`/chat` and `/review` work with any OpenAI-compatible API. To use a free local model via
[Ollama](https://ollama.com) instead of OpenAI, set in `.env`:

```
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=qwen2.5-coder:1.5b
OPENAI_API_KEY=ollama
```

(`OPENAI_API_KEY` can be any non-empty value — Ollama doesn't check it, but the OpenAI SDK
requires one to be set.) Run `ollama serve` and `ollama pull llama3.1` first. Leave
`OPENAI_BASE_URL` empty to use OpenAI's real API.

## Test

```bash
pytest
```
