"""Seeds the demo Bank Mitra accounts. Safe to run repeatedly."""

import asyncio

from app.core.config import get_settings
from app.services.container import build_container


async def main() -> None:
    container = build_container(get_settings())
    try:
        count = await container.auth_service.seed()
    finally:
        await container.close()
    print(f"{count} demo operators present")


if __name__ == "__main__":
    asyncio.run(main())
