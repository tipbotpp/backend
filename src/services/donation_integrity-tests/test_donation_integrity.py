import pytest

@pytest.mark.asyncio
async def test_donation_atomicity(donation_service, session, user, streamer):

    initial_user_balance = user.balance
    initial_streamer_balance = streamer.balance

    donation = await donation_service.send(
        user=user,
        streamer_id=streamer.telegram_id,
        amount=100,
        message="test"
    )

    # reload from DB
    updated_user = await get_user(session, user.telegram_id)
    updated_streamer = await get_user(session, streamer.telegram_id)

    donations = await get_donations(session, donation.id)
    transactions = await get_transactions(session, donation.id)

    # 1. donation exists
    assert donation is not None
    assert len(donations) == 1

    # 2. balances updated correctly
    assert updated_user.balance == initial_user_balance - 100
    assert updated_streamer.balance == initial_streamer_balance + 100

    # 3. transactions integrity
    sent = [t for t in transactions if t.type == "DONATION_SENT"]
    received = [t for t in transactions if t.type == "DONATION_RECEIVED"]

    assert len(sent) == 1
    assert len(received) == 1

    assert sent[0].amount == -100
    assert received[0].amount == 100