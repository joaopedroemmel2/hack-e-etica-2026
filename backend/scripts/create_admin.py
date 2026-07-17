import asyncio

from sqlmodel import select

from app.core.config import settings
from app.core.database import session_factory
from app.core.security import hash_password
from app.models.entities import Role, User


async def main() -> None:
    admin_name = settings.initial_admin_name
    admin_email = settings.initial_admin_email
    admin_password = settings.initial_admin_password

    if not all([admin_name, admin_email, admin_password]):
        print(
            "Administrador inicial não configurado. "
            "Defina INITIAL_ADMIN_NAME, INITIAL_ADMIN_EMAIL "
            "e INITIAL_ADMIN_PASSWORD."
        )
        return

    normalized_email = admin_email.strip().lower()

    async with session_factory() as session:
        existing = (
            await session.exec(
                select(User).where(User.email == normalized_email)
            )
        ).first()

        if existing:
            print("Administrador inicial já existe.")
            return

        admin = User(
            name=admin_name.strip(),
            email=normalized_email,
            password_hash=hash_password(admin_password),
            role=Role.ADMIN,
        )

        session.add(admin)
        await session.commit()

        print("Administrador inicial criado com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())