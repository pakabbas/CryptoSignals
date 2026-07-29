from __future__ import annotations

import json

from app.backtester.engine import BacktestEngine
from app.database import db
from app.models import BacktestResult, Coin, Strategy
from app.services.base import BaseService
from app.services.historical_download_service import HistoricalDownloadService
from app.utils.logging_setup import get_logger

logger = get_logger("strategy")


class BacktestService(BaseService[BacktestResult]):
    def __init__(self) -> None:
        self.downloader = HistoricalDownloadService()
        self.engine = BacktestEngine()

    def run(
        self,
        strategy_id: int,
        coin_id: int,
        period_days: int,
        *,
        download: bool = True,
    ) -> BacktestResult:
        strategy = Strategy.query.get_or_404(strategy_id)
        coin = Coin.query.get_or_404(coin_id)
        timeframe = strategy.timeframe

        if download:
            self.downloader.download_and_store(coin.id, coin.symbol, timeframe, period_days)

        df = self.downloader.dataframe_from_db(coin.id, timeframe, period_days)
        if df.empty:
            df = self.downloader.exchange.fetch_ohlcv_dataframe(coin.symbol, timeframe, limit=500)
        if df.empty:
            raise ValueError("No historical data available for backtest")

        output = self.engine.run(df, strategy.definition_json, timeframe)
        result = BacktestResult(
            strategy_id=strategy.id,
            coin_id=coin.id,
            timeframe=timeframe,
            period_days=period_days,
            metrics_json=output.metrics,
        )
        db.session.add(result)
        db.session.commit()
        logger.info("Backtest saved id=%s strategy=%s coin=%s", result.id, strategy.name, coin.symbol)
        return result

    def get(self, result_id: int) -> BacktestResult:
        return BacktestResult.query.get_or_404(result_id)

    def list_recent(self, limit: int = 50) -> list[BacktestResult]:
        return BacktestResult.query.order_by(BacktestResult.created_at.desc()).limit(limit).all()

    def export_json(self, result_id: int) -> str:
        result = self.get(result_id)
        payload = {
            "strategy_id": result.strategy_id,
            "coin_id": result.coin_id,
            "timeframe": result.timeframe,
            "period_days": result.period_days,
            "metrics": result.metrics_json,
            "created_at": result.created_at.isoformat() if result.created_at else None,
        }
        return json.dumps(payload, indent=2)

    def compare(self, result_ids: list[int]) -> list[BacktestResult]:
        if not result_ids:
            return []
        return (
            BacktestResult.query.filter(BacktestResult.id.in_(result_ids))
            .order_by(BacktestResult.created_at.desc())
            .all()
        )
