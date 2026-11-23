"""Seeds the demo Bank Mitra accounts. Safe to run repeatedly."""

import asyncio

from app.core.config import get_settings
from app.services.auth_service import SEED_OPERATORS
from app.services.container import build_container


async def main() -> None:
    container = build_container(get_settings())
    try:
        await container.auth_service.seed()
    finally:
        await container.close()
    print(f"seeded {len(SEED_OPERATORS)} operators")


if __name__ == "__main__":
    asyncio.run(main())
