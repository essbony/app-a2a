import logging
import os

from dotenv import load_dotenv

load_dotenv()

MODEL_ID = os.getenv('MODEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BASE_URL = os.getenv('BASE_URL')

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '10008'))
PUBLIC_URL = os.getenv("PUBLIC_URL")

# URL résolue de l'agent (AGENT_URL env > PUBLIC_URL normalisée > HOST:PORT)
_raw_agent_url = os.getenv("AGENT_URL")
if _raw_agent_url:
    AGENT_URL = _raw_agent_url
elif PUBLIC_URL:
    if PUBLIC_URL.startswith(("http://", "https://")):
        AGENT_URL = PUBLIC_URL
    else:
        AGENT_URL = f"https://{PUBLIC_URL}"
else:
    _host = HOST if HOST != "0.0.0.0" else "127.0.0.1"
    AGENT_URL = f"http://{_host}:{PORT}"

AGENT_URL = AGENT_URL.rstrip("/")

CLIENT_TIMEOUT = int(os.getenv("CLIENT_TIMEOUT", "60"))
CLIENT_RETRIES = int(os.getenv("CLIENT_RETRIES", "1"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
for noisy in ("httpx", "httpcore", "openai._base_client", "asyncio"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
LOG = logging.getLogger("client_a2a")


def get_agent_url() -> str:
    return AGENT_URL
