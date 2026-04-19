import asyncio
from app.db.session import engine
from app.models.all import Base, User, RoleEnum
from app.core.security import get_password_hash
from app.db.session import async_session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
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
        print("Database initialized and Admin created. Phone:", admin_phone, "Password: admin123")

if __name__ == "__main__":
    asyncio.run(init_db())
