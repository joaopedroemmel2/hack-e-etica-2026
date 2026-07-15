import asyncio

from sqlmodel import select

from app.core.config import settings
from app.core.database import session_factory
from app.core.security import hash_password
from app.models.entities import Role, User


async def main() -> None:
    if not all(
        [settings.initial_admin_name, settings.initial_admin_email, settings.initial_admin_password]
    ):
        raise SystemExit(
            "Configure INITIAL_ADMIN_NAME, INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD"
        )
    async with session_factory() as session:
        existing = (
            await session.exec(
                select(User).where(User.email == settings.initial_admin_email.lower())
            )
        ).first()
        if existing:
            raise SystemExit("Administrador já existe")
        session.add(
            User(
                name=settings.initial_admin_name,
                email=settings.initial_admin_email.lower(),
                password_hash=hash_password(settings.initial_admin_password),
                role=Role.ADMIN,
            )
        )
        await session.commit()
        print("Administrador criado com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())
