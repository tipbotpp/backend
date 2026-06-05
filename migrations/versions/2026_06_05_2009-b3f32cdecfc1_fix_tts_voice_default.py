"""fix_tts_voice_default

Revision ID: b3f32cdecfc1
Revises: 9370bad7e785
Create Date: 2026-06-05 20:09:43.309345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f32cdecfc1'
down_revision: Union[str, Sequence[str], None] = '9370bad7e785'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "alert_settings",
        "tts_voice",
        server_default="aidar",
    )
    op.execute("UPDATE alert_settings SET tts_voice = 'aidar' WHERE tts_voice = 'silero_v3_ru'")


def downgrade() -> None:
    op.alter_column(
        "alert_settings",
        "tts_voice",
        server_default="silero_v3_ru",
    )
    op.execute("UPDATE alert_settings SET tts_voice = 'silero_v3_ru' WHERE tts_voice = 'aidar'")
