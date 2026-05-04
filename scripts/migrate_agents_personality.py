import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    print("Starting migration: Adding personality_id to agents table...")
    async with engine.begin() as conn:
        try:
            # 1. Add personality_id column if it doesn't exist
            await conn.execute(text("""
                ALTER TABLE agents 
                ADD COLUMN IF NOT EXISTS personality_id UUID 
                REFERENCES personalities(id) ON DELETE SET NULL;
            """))
            print("Successfully added personality_id column to agents table")
            
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
