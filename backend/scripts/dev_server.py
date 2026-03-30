import os
import sys
from pathlib import Path

import uvicorn

BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(BASE_DIR)],
    )
