import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    command.upgrade(cfg, "head")
