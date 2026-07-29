from __future__ import annotations

from datetime import datetime, timezone

from app.models import Coin, Strategy
from app.services.candle_service import CandleService
from app.services.coin_service import CoinService
from app.services.exchange_service import ExchangeService, exchange_service_for_settings
from app.services.settings_service import SettingsService
from app.services.signal_service import SignalService
from app.services.strategy_service import StrategyService
from app.strategies.evaluator import StrategyEvaluator
from app.utils.logging_setup import get_logger

logger = get_logger("scanner")


class ScannerService:
    """Fetch candles, evaluate strategies, emit signals for enabled USDT pairs."""

    def __init__(self) -> None:
        self._exchange: ExchangeService | None = None
        self.candles = CandleService()
        self.coins = CoinService()
        self.strategies = StrategyService()
        self.signals = SignalService()
        self.evaluator = StrategyEvaluator()
        self.settings = SettingsService()

    @property
    def exchange(self) -> ExchangeService:
        if self._exchange is None:
            self._exchange = exchange_service_for_settings()
        return self._exchange

    def run_scan(self) -> dict[str, int]:
        stats = {"coins": 0, "strategies": 0, "signals": 0, "errors": 0}
        now = datetime.now(timezone.utc)

        try:
            enabled_coins = [c for c in self.coins.list_coins() if c.enabled]
            enabled_strategies = self.strategies.list_enabled()
            stats["coins"] = len(enabled_coins)
            stats["strategies"] = len(enabled_strategies)

            if not enabled_coins:
                self._update_status("idle — no enabled coins", now)
                return stats

            for coin in enabled_coins:
                coin_strategies = self.strategies.list_enabled_for_coin(coin.id)
                if not coin_strategies:
                    coin_strategies = enabled_strategies
                for strategy in coin_strategies:
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
        bars = self.exchange.fetch_ohlcv(coin.symbol, timeframe, limit=300)
        self.candles.upsert_bars(coin.id, timeframe, bars)
        df = self.exchange.fetch_ohlcv_dataframe(coin.symbol, timeframe, limit=300)
        if df.empty:
            return False

        result = self.evaluator.evaluate(df, strategy.definition_json, timeframe)
        if not result.signal_type:
            return False

        candle_time = result.candle_time.to_pydatetime()
        created = self.signals.create_and_notify(
            coin_id=coin.id,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            symbol=coin.symbol,
            signal_type=result.signal_type,
            timeframe=timeframe,
            price=result.price,
            candle_time=candle_time,
        )
        return created is not None

    def _update_status(self, status: str, now: datetime) -> None:
        self.settings.set_many(
            {
                "scanner_status": status,
                "last_scan_time": now.isoformat(),
            }
        )
