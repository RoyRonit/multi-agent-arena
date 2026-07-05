"""Central config. Everything tunable via env; one required var: OPENROUTER_API_KEY."""
import os

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
)

# One cheap/fast model runs all 5 personas; a stronger one chairs (judges + verdict).
# Override either via env without touching code.
AGENT_MODEL = os.environ.get("AGENT_MODEL", "google/gemini-2.5-flash")
CHAIRMAN_MODEL = os.environ.get("CHAIRMAN_MODEL", "anthropic/claude-sonnet-4.5")

# --- Debate shape ---
DEFAULT_ROUNDS = int(os.environ.get("ROUNDS", "3"))
TURN_WORD_CAP = int(os.environ.get("TURN_WORD_CAP", "150"))
TURN_MAX_TOKENS = int(os.environ.get("TURN_MAX_TOKENS", "320"))

# --- Economy (see PRD §6) ---
START_BALANCE = int(os.environ.get("START_BALANCE", "1000"))
BASE_FEE = int(os.environ.get("BASE_FEE", "50"))
TOKEN_RATE = float(os.environ.get("TOKEN_RATE", "0.1"))
WIN_REWARD = int(os.environ.get("WIN_REWARD", "300"))
RUNNERUP_REWARD = int(os.environ.get("RUNNERUP_REWARD", "100"))
REDUNDANCY_FINE = int(os.environ.get("REDUNDANCY_FINE", "100"))
REDUNDANCY_THRESHOLD = int(os.environ.get("REDUNDANCY_THRESHOLD", "7"))

# Judge scoring weights (turn_score used for ranking within a round)
W_NOVELTY = 0.4
W_EVIDENCE = 0.3
W_PERSUASION = 0.3
W_REDUNDANCY = 0.5

DEBATES_DIR = os.environ.get(
    "DEBATES_DIR", os.path.join(os.path.dirname(__file__), "..", "debates")
)

# --- Access gate ---
# Set ACCESS_PHRASE to require a shared password (shown to users as an ASCII captcha
# they must read + type). Leave empty to disable the gate entirely.
ACCESS_PHRASE = os.environ.get("ACCESS_PHRASE", "").strip()

# Optional bound on cost even if the URL leaks: max debates the server will run per
# rolling 24h window. 0 = unlimited.
DAILY_DEBATE_CAP = int(os.environ.get("DAILY_DEBATE_CAP", "0"))
