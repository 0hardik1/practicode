import asyncio

from app.config import get_settings
from app.db import async_session_maker, init_db
from app.services.problem_loader import seed_problems


async def main() -> None:
    await init_db()
    settings = get_settings()
    async with async_session_maker() as session:
        loaded = await seed_problems(session, settings.problems_dir)
    print(f"Seeded {loaded} problems from {settings.problems_dir}")


if __name__ == "__main__":
    asyncio.run(main())
