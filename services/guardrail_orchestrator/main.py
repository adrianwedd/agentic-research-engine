from __future__ import annotations

import uvicorn

from .app import app


if __name__ == "__main__":  # pragma: no cover - manual execution
    uvicorn.run(app, host="0.0.0.0", port=8085)
