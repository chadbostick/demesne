import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
MEMORY_WINDOW = 5           # last N agent actions passed as context
OUTPUT_DIR = "./output"
MAX_ERAS = 10               # game ends after this many eras
WIN_VP_THRESHOLD = 80       # VP needed to win immediately
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Strategy phase GM narration: "summary" | "narrative" | "off"
#   summary   — GM gets mechanical facts, writes 2-3 sentence historian recap (default)
#   narrative — GM gets full faction narrative texts and synthesizes
#   off       — no GM narration after strategy phase
STRATEGY_NARRATION_MODE = "summary"
