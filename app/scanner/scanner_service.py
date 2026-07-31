from __future__ import annotations

from datetime import datetime, timezone

from app.models import Coin, Strategy
from app.services.candle_service import CandleService
from app.services.coin_service import CoinService
from app.services.exchange_service import ExchangeService, exchange_service_for_coin
from app.services.settings_service import SettingsService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService
from app.strategies.evaluator import StrategyEvaluator
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


class ScannerService:
    """Fetch candles, evaluate strategies, emit signals for enabled USDT pairs."""

    def __init__(self) -> None:
        self._exchanges: dict[str, ExchangeService] = {}
        self.candles = CandleService()
        self.coins = CoinService()
        self.strategies = StrategyService()
        self.signals = SignalService()
        self.evaluator = StrategyEvaluator()
        self.settings = SettingsService()

    def _exchange_for(self, coin: Coin) -> ExchangeService:
        key = (coin.exchange or "kraken").strip().lower()
        if key not in self._exchanges:
            self._exchanges[key] = exchange_service_for_coin(coin)
        return self._exchanges[key]

    def run_scan(self) -> dict[str, int]:
        stats = {"coins": 0, "strategies": 0, "signals": 0, "errors": 0}
        now = datetime.now(timezone.utc)

        try:
            pairs = self.strategies.list_scan_pairs()
            stats["coins"] = len({coin.id for coin, _ in pairs})
            stats["strategies"] = len({strategy.id for _, strategy in pairs})

            if not pairs:
                self._update_status("idle — no strategy/coin pairs assigned", now)
                return stats

            for coin, strategy in pairs:
                try:
                    if self._scan_pair(coin, strategy):
                        stats["signals"] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    logger.exception(
                        "Scan failed coin=%s strategy=%s: %s",
                        coin.symbol,
                        strategy.name,
                        exc,
                    )

            self._update_status(
                f"running — last scan OK ({stats['signals']} new signals)",
                now,
            )
        except Exception as exc:
            stats["errors"] += 1
            logger.exception("Scanner run failed: %s", exc)
            self._update_status(f"error — {exc}", now)

        return stats

    def _scan_pair(self, coin: Coin, strategy: Strategy) -> bool:
        timeframe = strategy.timeframe or self.settings.get("default_timeframe", "1H")
        market = self._exchange_for(coin)
        bars = market.fetch_ohlcv(coin.symbol, timeframe, limit=300)
        self.candles.upsert_bars(coin.id, timeframe, bars)
        df = market.fetch_ohlcv_dataframe(coin.symbol, timeframe, limit=300)
        if df.empty:
            return False

        result = self.evaluator.evaluate(df, strategy.definition_json, timeframe)
        if not result.signal_type:
            return False

        enriched = self.evaluator._enrich_dataframe(df, strategy.definition_json)
        from app.strategies.scalp_management import (
            build_risk_levels,
            is_fresh_bb_touch,
            management_from_definition,
        )

        mgmt = management_from_definition(strategy.definition_json)
        if mgmt.get("fresh_bb_touch") and not is_fresh_bb_touch(
            enriched,
            result.bar_index,
            "long" if result.signal_type == "BUY" else "short",
        ):
            return False

        entry_price = result.price
        atr_bar = result.bar_index
        if str(mgmt.get("entry_fill", "close")).lower() == "next_open":
            next_i = result.bar_index + 1
            if next_i < len(enriched):
                entry_price = float(enriched["open"].iloc[next_i])
                atr_bar = result.bar_index

        atr = self.evaluator.atr_at_index(enriched, strategy.definition_json, atr_bar)
        stop_loss, take_profit = build_risk_levels(
            result.signal_type,
            entry_price,
            enriched,
            strategy.definition_json,
            atr_bar,
        )
        if stop_loss is None or take_profit is None:
            from app.risk.levels import levels_for_signal_alert

            levels = levels_for_signal_alert(
                result.signal_type,
                entry_price,
                definition=strategy.definition_json,
                atr=atr,
            )
            stop_loss, take_profit = levels.stop_loss, levels.take_profit

        candle_time = result.candle_time.to_pydatetime()
        created = self.signals.create_and_notify(
            coin_id=coin.id,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            symbol=coin.symbol,
            signal_type=result.signal_type,
            timeframe=timeframe,
            price=entry_price,
            candle_time=candle_time,
            stop_loss=stop_loss,
            take_profit=take_profit,
            definition=strategy.definition_json,
            atr=atr,
        )
        return created is not None

    def _update_status(self, status: str, now: datetime) -> None:
        self.settings.set_many(
            {
                "scanner_status": status,
                "last_scan_time": now.isoformat(),
            }
        )
