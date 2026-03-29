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

# Culture preference mode: "deterministic" | "llm"
#   deterministic — hardcoded preference tables (no API cost, default)
#   llm           — LLM generates preferences at faction creation (deferred)
CULTURE_PREFERENCE_MODE = "deterministic"

# Faction count range (random between min/max if --factions not specified)
MIN_FACTIONS = 2
MAX_FACTIONS = 5

# Dynamic faction addition (set of modes, can combine)
ADD_FACTIONS_MODES: set = set()

# Dynamic faction removal (set of modes, can combine)
REMOVE_FACTIONS_MODES: set = set()

# Display modes (overridden by CLI flags)
VERBOSE = False       # show metagame info (tokens, dice, decision trees)
ALL_PAUSES = False    # pause at every phase, not just end of era
