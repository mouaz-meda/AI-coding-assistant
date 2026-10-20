# Plain ANSI escape codes for this app's debug prints — no dependency needed
# for a local terminal. One color per [tag] so it's obvious at a glance which
# part of the app is printing.
# 256-color codes (\033[38;5;Nm) instead of the basic 8-color set — more hues
# to pick from, so each tag stays visually distinct instead of two of them
# both reading as "blue-ish" on a given terminal theme.
RESET = "\033[0m"
LLM = "\033[38;5;208m"  # orange
AGENT = "\033[38;5;213m"  # pink
VECTOR_STORE = "\033[38;5;220m"  # gold
INGEST = "\033[38;5;39m"  # azure blue
REVIEW = "\033[38;5;82m"  # bright green