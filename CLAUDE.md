# AI Coding Assistant — Project Guidelines

## Project

This is a learning project to build a professional, usable AI Coding Assistant.

The goal is to learn and apply:

* Python
* FastAPI
* SQL / relational databases
* OpenAI API and LLMs
* RAG
* LangChain
* Vector databases
* Gen AI application architecture

The application should eventually understand code/projects and assist developers with coding-related tasks.

---

## Development Philosophy

Prioritize:

1. Human-readable code
2. Simplicity
3. Maintainability
4. Clear architecture
5. Practical engineering over unnecessary abstraction

Prefer simple, explicit solutions over clever or overly abstract implementations.

Avoid:

* Premature optimization
* Over-engineering
* Unnecessary design patterns
* Unnecessary dependencies
* Complex abstractions that hide important concepts
* Implementing functionality before it is needed

When multiple approaches are reasonable, prefer the one that is easiest to understand and teaches the underlying concept clearly.

---

## Development Workflow

Build incrementally.

The high-level roadmap is:

1. Project structure and configuration
2. Database setup and user model
3. User registration
4. Login/logout and authentication
5. AI Coding Assistant architecture
6. LLM integration
7. Code/project ingestion
8. RAG pipeline
9. Vector database
10. LangChain integration where useful
11. Coding-assistant features
12. Testing, error handling, logging, and production improvements

Do not implement the entire roadmap at once.

For each phase:

1. Inspect the existing implementation.
2. Break the phase into small steps.
3. Show the steps before implementation.
4. Implement only the current step.
5. Run relevant tests/checks.
6. Summarize the changes briefly.
7. Wait for approval before continuing.

Do not silently implement future steps.

---

## Code Quality

Follow standard Python and FastAPI conventions.

Use:

* Clear names
* Small, focused functions
* Appropriate type hints
* Pydantic models where appropriate
* Clear separation of responsibilities
* Consistent error handling
* Tests for important behavior

Keep code readable without excessive comments.

Comments and docstrings should explain *why* something exists when the reason is not obvious, rather than explaining every line.

---

## Project Changes

Before modifying code:

* Inspect relevant existing files.
* Understand the current implementation.
* Do not assume files, APIs, or behavior that have not been verified.

When implementing a task:

* Modify only files necessary for the task.
* Do not refactor unrelated code.
* Do not introduce future functionality.
* Keep the application runnable.
* Prefer the smallest correct change.

If an important architectural decision is unclear, stop and present the options briefly instead of guessing.

---

## Dependencies

Keep dependencies minimal.

Do not add a library when the functionality can be implemented simply with the existing stack.

Before introducing a significant dependency, briefly explain why it is needed and what problem it solves.

---

## AI / RAG Development

When implementing AI functionality, keep the underlying concepts understandable.

Do not hide important concepts behind LangChain or other abstractions unnecessarily.

When practical, understand and implement the fundamental flow before adding framework abstractions.

For RAG, keep the concepts explicit:

Document → Chunking → Embeddings → Vector Storage → Retrieval → Context → LLM → Response

Use LangChain where it provides meaningful value, not simply because it is available.

---

## Testing

Keep the project verifiable after each meaningful change.

Run relevant tests after implementation.

When fixing a bug:

1. Identify the root cause.
2. Make the smallest correct change.
3. Run the relevant tests.
4. Do not perform unrelated refactoring.

---

## Communication

Keep explanations concise.

After implementation, report:

* Files changed
* What changed
* Important decisions
* Tests/checks performed
* Recommended next step

Do not provide long explanations unless requested.

---

## Important Rule

This is both a real software project and a learning project.

The final application should be professional and usable, but the implementation should remain understandable to a developer learning the technologies involved.
