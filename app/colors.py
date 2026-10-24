import logging

# 256-color ANSI codes (\033[38;5;Nm) — more hues to pick from than the basic
# 8-color set, so each module stays visually distinct instead of two of them
# both reading as "blue-ish" on a given terminal theme.
RESET = "\033[0m"
_COLOR_BY_LOGGER_PREFIX = {
    "app.ai.llm": "\033[38;5;208m",  # orange
    "app.ai.agent": "\033[38;5;213m",  # pink
    "app.ai.vector_store": "\033[38;5;220m",  # gold
    "app.ingestion": "\033[38;5;39m",  # azure blue
    "app.review": "\033[38;5;82m",  # bright green
}


class ColorFormatter(logging.Formatter):
    """Colors each log line by which app module logged it — same per-area
    colors the old hand-rolled print()s used, now picked from the logger
    name instead of being pasted into every call site."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for prefix, color in _COLOR_BY_LOGGER_PREFIX.items():
            if record.name.startswith(prefix):
                return f"{color}{message}{RESET}"
        return message


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])