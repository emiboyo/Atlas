from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from prometheus_client import generate_latest
from pydantic import ValidationError

from apps.api.src.research.engine import (
    DeterministicBacktestEngine,
    canonical_fingerprint,
    rate_of_change,
    rolling_volatility,
    simple_moving_average,
)
from apps.api.src.research.schemas import (
    BacktestCreate,
    ExplanationCreate,
    ResearchRule,
    StrategyCreate,
    VersionCreate,
)
from packages.database.atlas_database.models.enums import (
    CandleInterval,
    MarketDataStatus,
)
from packages.database.atlas_database.models.instruments import HistoricalCandle


def candles(values: list[str]) -> list[HistoricalCandle]:
    listing_id = uuid4()
    return [
        HistoricalCandle(
            id=uuid4(),
            listing_id=listing_id,
            provider="atlas_simulated",
            interval=CandleInterval.ONE_DAY,
            period_start=datetime(2026, 2, 1, tzinfo=UTC) + timedelta(days=index),
            period_end=datetime(2026, 2, 2, tzinfo=UTC) + timedelta(days=index),
            open=Decimal(value),
            high=Decimal(value) + 1,
            low=Decimal(value) - 1,
            close=Decimal(value),
            adjusted_close=Decimal(value),
            volume=100,
            currency="GBP",
            data_status=MarketDataStatus.SIMULATED,
            received_at=datetime(2026, 3, 1, tzinfo=UTC),
        )
        for index, value in enumerate(values)
    ]


def test_indicators_are_decimal_bounded_and_deterministic() -> None:
    values = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")]
    assert simple_moving_average(values, 2) == Decimal("3.5")
    assert rate_of_change(values, 2) == Decimal("100")
    assert rolling_volatility(values, 3) is not None
    assert simple_moving_average(values, 10) is None
    assert canonical_fingerprint({"b": 2, "a": 1}) == canonical_fingerprint({"a": 1, "b": 2})


def test_engine_replays_identically_without_lookahead() -> None:
    series = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    engine = DeterministicBacktestEngine()
    kwargs = dict(
        starting_capital=Decimal("1000"),
        rule_id="cross",
        short_window=2,
        long_window=3,
        execution_policy="next_open",
        fee_model="fixed_amount_per_event",
        fee_value=Decimal("1"),
        slippage_bps=Decimal("10"),
        sizing_policy="fixed_percentage_of_available_simulated_cash",
        sizing_value=Decimal("50"),
    )
    first = engine.run(series, **kwargs)
    second = engine.run(series, **kwargs)
    assert first.result_checksum == second.result_checksum
    assert first.events == second.events
    assert all(event.execution_index >= event.decision_index for event in first.events)
    changed = engine.run(series, **{**kwargs, "fee_value": Decimal("2")})
    assert changed.result_checksum != first.result_checksum


def test_strict_research_schemas_and_bounds() -> None:
    rule = ResearchRule(id="cross", rule_type="sma_crossover", short_window=2, long_window=3)
    assert rule.schema_version == 1
    with pytest.raises(ValidationError):
        ResearchRule(id="bad", rule_type="sma_crossover", short_window=4, long_window=3)
    with pytest.raises(ValidationError):
        StrategyCreate(
            tenant_id=uuid4(),
            name="Research",
            research_purpose="Historical only",
            status="active",  # type: ignore[call-arg]
        )


@pytest.mark.parametrize("policy", ["skip_event", "skip_observation", "arbitrary"])
def test_unsupported_missing_data_policies_fail_validation(policy: str) -> None:
    with pytest.raises(ValidationError):
        BacktestCreate(
            strategy_id=uuid4(),
            strategy_version_id=uuid4(),
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 2),
            starting_capital=Decimal("100"),
            fee_model="zero_fee",
            slippage_model="zero_slippage",
            execution_policy="next_open",
            sizing_policy="fixed_quantity",
            sizing_value=Decimal("1"),
            missing_data_policy=policy,  # type: ignore[arg-type]
        )


def test_safe_missing_data_policy_is_the_only_default() -> None:
    value = BacktestCreate(
        strategy_id=uuid4(),
        strategy_version_id=uuid4(),
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 2),
        starting_capital=Decimal("100"),
        fee_model="zero_fee",
        slippage_model="zero_slippage",
        execution_policy="next_open",
        sizing_policy="fixed_quantity",
        sizing_value=Decimal("1"),
    )
    assert value.missing_data_policy == "fail_run"


def test_research_metrics_have_only_bounded_labels_and_documented_buckets() -> None:
    from apps.api.src.research.metrics import (
        BACKTEST_DURATION,
        BACKTESTS,
        DATA_QUALITY,
        EXPLANATIONS,
        RESEARCH_CONFLICTS,
        STRATEGY_OPERATIONS,
    )

    assert STRATEGY_OPERATIONS._labelnames == ("operation", "outcome")
    assert BACKTESTS._labelnames == ("outcome",)
    assert DATA_QUALITY._labelnames == ("outcome",)
    assert EXPLANATIONS._labelnames == ("outcome",)
    assert RESEARCH_CONFLICTS._labelnames == ("operation",)
    assert BACKTEST_DURATION._labelnames == ()
    exposed = generate_latest().decode()
    for name in (
        "atlas_research_strategy_operations",
        "atlas_research_backtests",
        "atlas_research_backtest_duration_seconds",
        "atlas_research_conflicts",
        "atlas_research_explanations",
        "atlas_research_data_quality",
    ):
        assert name in exposed
    with pytest.raises(ValidationError):
        BacktestCreate(
            strategy_id=uuid4(),
            strategy_version_id=uuid4(),
            start_date=date(2026, 2, 2),
            end_date=date(2026, 2, 1),
            starting_capital=Decimal("100"),
            fee_model="zero_fee",
            slippage_model="zero_slippage",
            execution_policy="next_open",
            sizing_policy="fixed_quantity",
            sizing_value=Decimal("1"),
            missing_data_policy="fail_run",
        )


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (
            StrategyCreate,
            {
                "tenant_id": str(uuid4()),
                "name": "Protected",
                "research_purpose": "Mass-assignment evidence",
                "created_by_user_id": str(uuid4()),
            },
        ),
        (
            VersionCreate,
            {
                "version_label": "Protected",
                "base_currency": "GBP",
                "listing_id": str(uuid4()),
                "version_number": 99,
                "configuration_fingerprint": "client-controlled",
                "rules": [
                    {
                        "id": "cross",
                        "rule_type": "sma_crossover",
                        "short_window": 2,
                        "long_window": 3,
                    }
                ],
            },
        ),
        (
            BacktestCreate,
            {
                "strategy_id": str(uuid4()),
                "strategy_version_id": str(uuid4()),
                "start_date": "2026-01-01",
                "end_date": "2026-01-10",
                "starting_capital": "1000",
                "fee_model": "zero_fee",
                "slippage_model": "zero_slippage",
                "execution_policy": "next_open",
                "sizing_policy": "fixed_quantity",
                "sizing_value": "1",
                "missing_data_policy": "fail_run",
                "status": "completed",
                "result_checksum": "client-controlled",
            },
        ),
        (
            ExplanationCreate,
            {
                "explanation_type": "run_summary",
                "status": "completed",
                "output_fingerprint": "client-controlled",
            },
        ),
        (
            ResearchRule,
            {
                "id": "cross",
                "rule_type": "python",
                "short_window": 2,
                "long_window": 3,
                "source": "__import__('os').system('whoami')",
            },
        ),
    ],
)
def test_protected_and_executable_fields_fail_closed(schema, payload) -> None:
    with pytest.raises(ValidationError):
        schema.model_validate(payload)


def engine_arguments() -> dict[str, object]:
    return {
        "starting_capital": Decimal("1000"),
        "rule_id": "cross",
        "short_window": 2,
        "long_window": 3,
        "execution_policy": "next_open",
        "fee_model": "zero_fee",
        "fee_value": Decimal("0"),
        "slippage_bps": Decimal("0"),
        "sizing_policy": "fixed_percentage_of_available_simulated_cash",
        "sizing_value": Decimal("50"),
    }


def causal_events(simulation, before_index: int):
    return [
        event
        for event in simulation.events
        if event.decision_index < before_index and event.rule_ids != ["end_of_historical_period"]
    ]


def test_future_candle_injection_cannot_change_prior_decisions() -> None:
    original = candles(["10", "9", "8", "9", "10", "8", "7", "9"])
    injected = [*original, candles(["1000"])[0]]
    injected[-1].listing_id = original[0].listing_id
    injected[-1].period_start = original[-1].period_start + timedelta(days=1)
    injected[-1].period_end = original[-1].period_end + timedelta(days=1)
    engine = DeterministicBacktestEngine()
    baseline = engine.run(original, **engine_arguments())  # type: ignore[arg-type]
    with_future = engine.run(injected, **engine_arguments())  # type: ignore[arg-type]
    assert causal_events(with_future, len(original)) == causal_events(baseline, len(original))


def test_out_of_order_observations_are_canonically_ordered() -> None:
    ordered = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    shuffled = [ordered[index] for index in (8, 2, 5, 0, 7, 1, 6, 4, 3)]
    engine = DeterministicBacktestEngine()
    baseline = engine.run(ordered, **engine_arguments())  # type: ignore[arg-type]
    replay = engine.run(shuffled, **engine_arguments())  # type: ignore[arg-type]
    assert replay.events == baseline.events
    assert replay.equity == baseline.equity
    assert replay.result_checksum == baseline.result_checksum


def test_full_series_normalization_cannot_leak_future_value_into_prior_signals() -> None:
    baseline_series = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    altered_future = candles(["10", "9", "8", "9", "10", "8", "7", "9", "999999"])
    engine = DeterministicBacktestEngine()
    baseline = engine.run(baseline_series, **engine_arguments())  # type: ignore[arg-type]
    altered = engine.run(altered_future, **engine_arguments())  # type: ignore[arg-type]
    assert causal_events(altered, 8) == causal_events(baseline, 8)


def test_target_derived_fields_cannot_influence_rule_features() -> None:
    baseline_series = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    altered_targets = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    for item in altered_targets:
        item.high = Decimal("999999")
        item.low = Decimal("0.000001")
        item.adjusted_close = Decimal("500000")
        item.volume = 999999999
    engine = DeterministicBacktestEngine()
    baseline = engine.run(baseline_series, **engine_arguments())  # type: ignore[arg-type]
    altered = engine.run(altered_targets, **engine_arguments())  # type: ignore[arg-type]
    assert altered.events == baseline.events
    assert [item.total for item in altered.equity] == [item.total for item in baseline.equity]
    assert altered.data_fingerprint != baseline.data_fingerprint


def test_missing_observation_is_not_filled_from_future_data() -> None:
    complete = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    missing = [*complete[:4], *complete[5:]]
    simulation = DeterministicBacktestEngine().run(
        missing,
        **engine_arguments(),  # type: ignore[arg-type]
    )
    assert len(simulation.equity) == len(missing)
    assert all(point.index < len(missing) for point in simulation.equity)
    assert complete[4].id not in {
        observation_id
        for event in simulation.events
        for observation_id in (
            missing[event.decision_index].id,
            missing[event.execution_index].id,
        )
    }


def test_decision_and_execution_indices_never_use_later_observations() -> None:
    series = candles(["10", "9", "8", "9", "10", "8", "7", "9", "11"])
    simulation = DeterministicBacktestEngine().run(
        series,
        **engine_arguments(),  # type: ignore[arg-type]
    )
    for event in simulation.events:
        decision = series[event.decision_index]
        execution = series[event.execution_index]
        assert event.execution_index >= event.decision_index
        assert execution.period_start >= decision.period_start
        if event.rule_ids != ["end_of_historical_period"]:
            assert event.execution_index == event.decision_index + 1
