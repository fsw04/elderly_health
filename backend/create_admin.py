import asyncio
from app.db.session import async_session
from app.models.all import User, RoleEnum
from app.core.security import get_password_hash

async def create_admin():
    async with async_session() as session:
        admin_phone = "13800138000"
        admin = User(
            phone=admin_phone,
            role=RoleEnum.ADMIN,
            name="Admin Doctor",
            password_hash=get_password_hash("admin123")
        )
        session.add(admin)
        await session.commit()
        print("Admin created. Phone:", admin_phone, "Password: admin123")

if __name__ == "__main__":
    asyncio.run(create_admin())
