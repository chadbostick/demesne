import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-6"
MEMORY_WINDOW = 5           # last N agent actions passed as context
OUTPUT_DIR = "./output"
MAX_ERAS = 10               # game ends after this many eras
WIN_VP_THRESHOLD = 80       # VP needed to win immediately
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
