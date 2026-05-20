import asyncio
from app.db.session import AsyncSessionLocal
from app.services.auth_service import AuthService

async def main():
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        try:
            user = await auth_service.register(
                email="admin@relayforge.io",
                full_name="System Administrator",
                password="Password12345!",
                organization_name="Acme Corp"
            )
            await session.commit()
            print("Successfully seeded admin user: admin@relayforge.io / Password12345!")
        except ValueError as e:
            print("Seeding skipped or already seeded:", e)

if __name__ == "__main__":
    asyncio.run(main())
