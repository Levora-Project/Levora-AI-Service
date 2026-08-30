
import asyncio
import secrets
import sys

from prisma import Prisma

from src.modules.core.auth.api_key_auth import hash_key


async def create_key(name: str) -> None:
    raw_key = f"lv_{secrets.token_urlsafe(32)}"

    db = Prisma()
    await db.connect()
    try:
        record = await db.apikey.create(
            data={"key": hash_key(raw_key), "name": name, "is_active": True}
        )
    finally:
        await db.disconnect()

    print("\nAPI key created.")
    print(f"  name: {record.name}")
    print(f"  id:   {record.id}")
    print(f"\n  key:  {raw_key}")
    print("\nStore this key now. It cannot be recovered later.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python scripts/generate_api_key.py "<name>"')
        raise SystemExit(1)

    asyncio.run(create_key(sys.argv[1]))