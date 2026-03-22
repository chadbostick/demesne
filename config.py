import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-6"
MEMORY_WINDOW = 5       # last N agent actions passed as context
OUTPUT_DIR = "./output"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
