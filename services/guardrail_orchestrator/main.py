
# Security: Only bind to all interfaces in production
import os
HOST = HOST if os.getenv("ENVIRONMENT") == "production" else "127.0.0.1"
from __future__ import annotations

import uvicorn

from .app import app

if __name__ == "__main__":  # pragma: no cover - manual execution
    uvicorn.run(app, host=HOST, port=8085)
