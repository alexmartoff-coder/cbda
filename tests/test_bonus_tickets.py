import asyncio
import os
from db.db import init_db, issue_ticket, update_ticket_result, get_leaderboard, get_total_tickets_count, add_user
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock, MagicMock

async def test_bonus_tickets():
    # Setup fresh DB
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")

    await init_db()

    user_id = 12345
    await add_user(user_id, "testuser", "Test User")

    # Mock Bot and State
    bot = AsyncMock()
    state = AsyncMock()

    # 1. Test 10/10 -> +3 bonus
    ticket_num = await issue_ticket(user_id, "paid")
    # Mock get_quiz_session to return 10 score
    from db.db import set_quiz_session
    await set_quiz_session(user_id, ticket_num, score=10, current_question=10, is_active=True)

    await finish_quiz_logic(bot, state, user_id)

    total = await get_total_tickets_count()
    print(f"Total tickets after 10/10: {total} (Expected: 4)")
    assert total == 4

    # 2. Test 9/10 -> +2 bonus
    ticket_num = await issue_ticket(user_id, "paid")
    await set_quiz_session(user_id, ticket_num, score=9, current_question=10, is_active=True)
    await finish_quiz_logic(bot, state, user_id)

    total = await get_total_tickets_count()
    print(f"Total tickets after 9/10: {total} (Expected: 7)") # 4 + 1 + 2
    assert total == 7

    # 3. Test 8/10 -> +1 bonus
    ticket_num = await issue_ticket(user_id, "paid")
    await set_quiz_session(user_id, ticket_num, score=8, current_question=10, is_active=True)
    await finish_quiz_logic(bot, state, user_id)

    total = await get_total_tickets_count()
    print(f"Total tickets after 8/10: {total} (Expected: 9)") # 7 + 1 + 1
    assert total == 9

    # 4. Test 7/10 -> no bonus
    ticket_num = await issue_ticket(user_id, "paid")
    await set_quiz_session(user_id, ticket_num, score=7, current_question=10, is_active=True)
    await finish_quiz_logic(bot, state, user_id)

    total = await get_total_tickets_count()
    print(f"Total tickets after 7/10: {total} (Expected: 10)") # 9 + 1 + 0
    assert total == 10

    # 5. Leaderboard aggregation
    leaderboard = await get_leaderboard()
    print(f"Leaderboard for user 12345: {leaderboard[0][2]} (Expected: 10)")
    assert leaderboard[0][2] == 10

    print("Bonus tickets test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_bonus_tickets())
