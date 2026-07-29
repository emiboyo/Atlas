from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from hashlib import sha256
from itertools import pairwise

from packages.database.atlas_database.models.instruments import HistoricalCandle

Q = Decimal("0.000000000000000001")
ENGINE_VERSION = "atlas-deterministic-backtest/1"


def q(value: Decimal) -> Decimal:
    return value.quantize(Q, rounding=ROUND_HALF_EVEN)


def canonical_fingerprint(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def simple_moving_average(values: list[Decimal], window: int) -> Decimal | None:
    if window < 1 or len(values) < window:
        return None
    return q(sum(values[-window:], Decimal("0")) / Decimal(window))


def rate_of_change(values: list[Decimal], periods: int) -> Decimal | None:
    if periods < 1 or len(values) <= periods or values[-periods - 1] == 0:
        return None
    return q((values[-1] / values[-periods - 1] - 1) * 100)


def rolling_volatility(values: list[Decimal], window: int) -> Decimal | None:
    if len(values) < window + 1:
        return None
    returns = [
        current / previous - 1
        for previous, current in pairwise(values[-window - 1 :])
        if previous != 0
    ]
    if len(returns) < 2:
        return None
    mean = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum(((item - mean) ** 2 for item in returns), Decimal("0")) / Decimal(
        len(returns) - 1
    )
    with localcontext() as context:
        context.prec = 38
        return q(variance.sqrt() * 100)


@dataclass(frozen=True)
class SimEvent:
    event_type: str
    decision_index: int
    execution_index: int
    price: Decimal
    quantity: Decimal
    gross: Decimal
    fee: Decimal
    slippage: Decimal
    cash_before: Decimal
    cash_after: Decimal
    position_before: Decimal
    position_after: Decimal
    rule_ids: list[str]


@dataclass(frozen=True)
class Equity:
    index: int
    cash: Decimal
    position_value: Decimal
    total: Decimal
    peak: Decimal
    drawdown_amount: Decimal
    drawdown_percentage: Decimal


@dataclass(frozen=True)
class Simulation:
    events: list[SimEvent]
    equity: list[Equity]
    ending_value: Decimal
    pnl: Decimal
    historical_return: Decimal
    maximum_drawdown: Decimal
    volatility: Decimal | None
    turnover: Decimal
    data_fingerprint: str
    result_checksum: str


class DeterministicBacktestEngine:
    def run(
        self,
        candles: list[HistoricalCandle],
        *,
        starting_capital: Decimal,
        rule_id: str,
        short_window: int,
        long_window: int,
        execution_policy: str,
        fee_model: str,
        fee_value: Decimal,
        slippage_bps: Decimal,
        sizing_policy: str,
        sizing_value: Decimal,
    ) -> Simulation:
        ordered = sorted(candles, key=lambda item: (item.period_start, item.id))
        if len({item.period_start for item in ordered}) != len(ordered):
            raise ValueError("duplicate historical observation timestamp")
        if len(ordered) < long_window + 1:
            raise ValueError("insufficient historical data")
        closes: list[Decimal] = []
        signals: list[tuple[int, bool]] = []
        previous_relation: bool | None = None
        for index, candle in enumerate(ordered):
            closes.append(candle.close)
            short = simple_moving_average(closes, short_window)
            long = simple_moving_average(closes, long_window)
            if short is None or long is None:
                continue
            relation = short > long
            if previous_relation is not None and relation != previous_relation:
                signals.append((index, relation))
            previous_relation = relation

        cash = q(starting_capital)
        position = Decimal("0")
        events: list[SimEvent] = []
        pending = list(signals)
        for decision_index, enter in pending:
            execution_index = (
                decision_index if execution_policy == "same_close" else decision_index + 1
            )
            if execution_index >= len(ordered):
                continue
            candle = ordered[execution_index]
            raw_price = candle.open if execution_policy == "next_open" else candle.close
            direction = Decimal("1") if enter else Decimal("-1")
            slip = q(raw_price * slippage_bps / Decimal("10000"))
            price = q(raw_price + slip * direction)
            if enter and position == 0:
                if sizing_policy == "fixed_simulated_cash_amount":
                    allocation = min(cash, sizing_value)
                    quantity = q(allocation / price)
                elif sizing_policy == "fixed_percentage_of_available_simulated_cash":
                    allocation = q(cash * sizing_value / Decimal("100"))
                    quantity = q(allocation / price)
                else:
                    quantity = sizing_value
                gross = q(quantity * price)
                fee = self._fee(gross, fee_model, fee_value)
                if quantity <= 0 or gross + fee > cash:
                    continue
                before_cash, before_position = cash, position
                cash = q(cash - gross - fee)
                position = q(position + quantity)
                events.append(
                    SimEvent(
                        "simulated_entry",
                        decision_index,
                        execution_index,
                        price,
                        quantity,
                        gross,
                        fee,
                        q(slip * quantity),
                        before_cash,
                        cash,
                        before_position,
                        position,
                        [rule_id],
                    )
                )
            elif not enter and position > 0:
                quantity = position
                gross = q(quantity * price)
                fee = self._fee(gross, fee_model, fee_value)
                before_cash, before_position = cash, position
                cash = q(cash + gross - fee)
                position = Decimal("0")
                events.append(
                    SimEvent(
                        "simulated_exit",
                        decision_index,
                        execution_index,
                        price,
                        quantity,
                        gross,
                        fee,
                        q(abs(slip) * quantity),
                        before_cash,
                        cash,
                        before_position,
                        position,
                        [rule_id],
                    )
                )

        if position > 0:
            index = len(ordered) - 1
            price = ordered[index].close
            gross = q(position * price)
            fee = self._fee(gross, fee_model, fee_value)
            events.append(
                SimEvent(
                    "simulated_exit",
                    index,
                    index,
                    price,
                    position,
                    gross,
                    fee,
                    Decimal("0"),
                    cash,
                    q(cash + gross - fee),
                    position,
                    Decimal("0"),
                    ["end_of_historical_period"],
                )
            )
            cash = events[-1].cash_after
            position = Decimal("0")

        events_by_execution = {event.execution_index: event for event in events}
        equity: list[Equity] = []
        replay_cash = q(starting_capital)
        replay_position = Decimal("0")
        peak = replay_cash
        for index, candle in enumerate(ordered):
            if event := events_by_execution.get(index):
                replay_cash, replay_position = event.cash_after, event.position_after
            total = q(replay_cash + replay_position * candle.close)
            peak = max(peak, total)
            drawdown = q(total - peak)
            drawdown_pct = q(drawdown / peak * 100) if peak else Decimal("0")
            equity.append(
                Equity(
                    index,
                    replay_cash,
                    q(replay_position * candle.close),
                    total,
                    peak,
                    drawdown,
                    drawdown_pct,
                )
            )
        ending = equity[-1].total
        pnl = q(ending - starting_capital)
        historical_return = q(pnl / starting_capital * 100)
        volatility = rolling_volatility([item.total for item in equity], len(equity) - 1)
        turnover = q(sum((event.gross for event in events), Decimal("0")) / starting_capital * 100)
        data_fp = canonical_fingerprint(
            [
                (str(item.id), item.period_start.isoformat(), str(item.open), str(item.close))
                for item in ordered
            ]
        )
        result_payload = {
            "events": [event.__dict__ for event in events],
            "equity": [item.__dict__ for item in equity],
            "data_fingerprint": data_fp,
            "engine": ENGINE_VERSION,
        }
        return Simulation(
            events,
            equity,
            ending,
            pnl,
            historical_return,
            min((item.drawdown_percentage for item in equity), default=Decimal("0")),
            volatility,
            turnover,
            data_fp,
            canonical_fingerprint(result_payload),
        )

    @staticmethod
    def _fee(gross: Decimal, model: str, value: Decimal) -> Decimal:
        if model == "zero_fee":
            return Decimal("0")
        if model == "fixed_amount_per_event":
            return q(value)
        return q(gross * value / Decimal("100"))
