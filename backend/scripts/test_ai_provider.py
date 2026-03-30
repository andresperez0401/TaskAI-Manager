import asyncio
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

from modules.ai.service import AiService  # noqa: E402


async def main() -> None:
    service = AiService()
    result = await service.test_provider_chat("Responde con OK y fecha actual")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
