import asyncio
import os
from db.db import init_db, issue_ticket, update_ticket_result, get_total_tickets_count

async def test_bonus_tickets():
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")

    await init_db()
    user_id = 12345

    # 1. Test 10 correct answers (+3 bonus)
    score = 10
    bonus_tickets = 3

    # Base ticket
    base_num = await issue_ticket(user_id, "paid")
    print(f"Issued base ticket: {base_num}")

    issued_bonus = []
    for _ in range(bonus_tickets):
        b_num = await issue_ticket(user_id, "bonus", status="completed")
        if b_num:
            issued_bonus.append(b_num)

    await update_ticket_result(base_num, "completed", score)

    total = await get_total_tickets_count()
    print(f"Total tickets after 10/10: {total} (Expected: 4)")
    print(f"Bonus tickets: {issued_bonus}")

    assert total == 4
    assert len(issued_bonus) == 3

    # 2. Test 8 correct answers (+1 bonus)
    score = 8
    bonus_tickets = 1

    base_num2 = await issue_ticket(user_id, "paid")
    issued_bonus2 = []
    for _ in range(bonus_tickets):
        b_num = await issue_ticket(user_id, "bonus", status="completed")
        if b_num:
            issued_bonus2.append(b_num)

    await update_ticket_result(base_num2, "completed", score)

    total = await get_total_tickets_count()
    print(f"Total tickets after 8/10: {total} (Expected: 6)")

    assert total == 6

    print("Bonus tickets test passed!")

if __name__ == "__main__":
    asyncio.run(test_bonus_tickets())
