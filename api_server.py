"""Kyvra HTTP API server entrypoint.

Usage:
  python api_server.py               # dev mode, port 8000
  uvicorn api_server:app --port 8000 # production

Environment variables:
  API_KEY   — Bearer token required on all requests (leave unset for open dev mode)
  API_PORT  — port to bind (default 8000)
  API_HOST  — host to bind (default 0.0.0.0)
"""

import logging
import os

import services.memory as memory
from interfaces.web.app import app  # re-export for uvicorn

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

memory.init_db()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    logging.getLogger(__name__).info("Starting Kyvra API on %s:%s", host, port)
    uvicorn.run("api_server:app", host=host, port=port, reload=False)
