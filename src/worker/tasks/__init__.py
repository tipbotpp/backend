from src.worker.tasks.donations import process_donation_media

# TODO: добавить passive_income_task — периодически начислять монеты зрителям
#       активных стримов согласно PassiveIncomeSettings (coins_per_interval / interval_minutes)

__all__ = ["process_donation_media"]
