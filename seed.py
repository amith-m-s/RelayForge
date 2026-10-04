import asyncio
import os

from app.db.session import AsyncSessionLocal
from app.services.auth_service import AuthService


async def main():
    password = os.getenv("SEED_ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("SEED_ADMIN_PASSWORD must be set before running the seed script")

    email = os.getenv("SEED_ADMIN_EMAIL", "admin@relayforge.local")
    full_name = os.getenv("SEED_ADMIN_NAME", "System Administrator")
    organization_name = os.getenv("SEED_ORGANIZATION", "Acme Corp")

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        try:
            await auth_service.register(
                email=email,
                full_name=full_name,
                password=password,
                organization_name=organization_name,
            )
            await session.commit()
            print(f"Successfully seeded admin user: {email}")
        except ValueError as exc:
            print("Seeding skipped or already seeded:", exc)


if __name__ == "__main__":
    asyncio.run(main())
