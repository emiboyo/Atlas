"""Harden persisted market-data numeric integrity.

Revision ID: 20260727_0005
Revises: 20260727_0004
Create Date: 2026-07-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260727_0005"
down_revision: str | None = "20260727_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


QUOTE_CHECKS = {
    "ck_quote_observations_bid_size_non_negative": "bid_size IS NULL OR bid_size >= 0",
    "ck_quote_observations_ask_size_non_negative": "ask_size IS NULL OR ask_size >= 0",
    "ck_quote_observations_open_non_negative": "open IS NULL OR open >= 0",
    "ck_quote_observations_high_non_negative": "high IS NULL OR high >= 0",
    "ck_quote_observations_low_non_negative": "low IS NULL OR low >= 0",
    "ck_quote_observations_previous_close_non_negative": (
        "previous_close IS NULL OR previous_close >= 0"
    ),
    "ck_quote_observations_delay_non_negative": (
        "delay_seconds IS NULL OR delay_seconds >= 0"
    ),
    "ck_quote_observations_currency_iso_length": "length(currency) = 3",
}

CANDLE_CHECKS = {
    "ck_historical_candles_adjusted_close_non_negative": (
        "adjusted_close IS NULL OR adjusted_close >= 0"
    ),
    "ck_historical_candles_currency_iso_length": "length(currency) = 3",
}


def upgrade() -> None:
    for name, condition in QUOTE_CHECKS.items():
        op.create_check_constraint(name, "quote_observations", condition)
    for name, condition in CANDLE_CHECKS.items():
        op.create_check_constraint(name, "historical_candles", condition)


def downgrade() -> None:
    for name in reversed(CANDLE_CHECKS):
        op.drop_constraint(name, "historical_candles", type_="check")
    for name in reversed(QUOTE_CHECKS):
        op.drop_constraint(name, "quote_observations", type_="check")
