import asyncio
import aiosqlite
import random
from db.db import DB_PATH, init_db

async def seed_data(target_real_count=2495):
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Create a dummy user for the seed tickets
        dummy_uid = 999999
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, accepted_rules) VALUES (?, ?, ?, 1)",
                         (dummy_uid, "seed_bot", "Seed User"))

        # 2. Check current paid tickets count
        async with db.execute("SELECT COUNT(*) FROM tickets WHERE type = 'paid'") as cursor:
            current_real_count = (await cursor.fetchone())[0]

        needed = target_real_count - current_real_count

        if needed <= 0:
            print(f"Already have {current_real_count} paid tickets. No seeding needed for target {target_real_count}.")
            return

        print(f"Seeding {needed} tickets to reach {target_real_count}...")

        # 3. Get available ticket numbers
        async with db.execute("SELECT ticket_number FROM available_tickets LIMIT ?", (needed,)) as cursor:
            rows = await cursor.fetchall()
            available_nums = [r[0] for r in rows]

        if len(available_nums) < needed:
            print(f"Not enough available tickets in pool! Found {len(available_nums)}")
            return

        # 4. Insert tickets in batches
        batch_size = 500
        for i in range(0, len(available_nums), batch_size):
            batch = available_nums[i:i+batch_size]
            ticket_data = [(dummy_uid, num, 'paid', 'failed', 0) for num in batch]

            await db.executemany(
                "INSERT INTO tickets (user_id, ticket_number, type, status, score) VALUES (?, ?, ?, ?, ?)",
                ticket_data
            )

            # Remove from available
            await db.executemany(
                "DELETE FROM available_tickets WHERE ticket_number = ?",
                [(num,) for num in batch]
            )

            print(f"Inserted {i + len(batch)}/{needed}...")
            await db.commit()

    print(f"✅ Seeding complete. Display count should now be 2495 (Real paid: {target_real_count}).")

if __name__ == "__main__":
    asyncio.run(seed_data())
