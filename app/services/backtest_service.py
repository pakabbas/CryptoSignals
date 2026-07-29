from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from app.backtester.engine import BacktestEngine
from app.database import db
from app.models import BacktestResult, Coin, Strategy
from app.services.base import BaseService
from app.services.exchange_service import exchange_service_for_coin
from app.services.historical_download_service import HistoricalDownloadService
from app.utils.logging_setup import get_logger

logger = get_logger("strategy")

MAX_CHART_POINTS = 1200


def trim_chart_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Keep DB rows and HTML responses bounded for long backtests."""
    out = dict(metrics)
    for key, max_len in (
        ("candles", MAX_CHART_POINTS),
        ("equity_curve", MAX_CHART_POINTS),
        ("drawdown_curve", MAX_CHART_POINTS),
        ("markers", 500),
    ):
        arr = out.get(key)
        if isinstance(arr, list) and len(arr) > max_len:
            step = max(1, len(arr) // max_len)
            out[key] = arr[::step][:max_len]
    return out


def chart_payload_from_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    trimmed = trim_chart_metrics(metrics)
    return {
        "candles": trimmed.get("candles", []),
        "markers": trimmed.get("markers", []),
        "equity_curve": trimmed.get("equity_curve", []),
        "drawdown_curve": trimmed.get("drawdown_curve", []),
    }


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
            self.downloader.download_and_store(
                coin.id,
                coin.symbol,
                timeframe,
                period_days,
                exchange_id=coin.exchange,
            )

        df = self.downloader.dataframe_from_db(coin.id, timeframe, period_days)
        if df.empty:
            market = exchange_service_for_coin(coin)
            df = market.fetch_ohlcv_dataframe(coin.symbol, timeframe, limit=500)
        if df.empty:
            raise ValueError("No historical data available for backtest")

        output = self.engine.run(df, strategy.definition_json, timeframe)
        metrics = trim_chart_metrics(output.metrics)
        result = BacktestResult(
            strategy_id=strategy.id,
            coin_id=coin.id,
            timeframe=timeframe,
            period_days=period_days,
            metrics_json=metrics,
        )
        db.session.add(result)
        db.session.commit()
        logger.info("Backtest saved id=%s strategy=%s coin=%s", result.id, strategy.name, coin.symbol)
        return result

    def get(self, result_id: int) -> BacktestResult:
        return BacktestResult.query.get_or_404(result_id)

    def list_recent(self, limit: int = 50) -> list[BacktestResult]:
        return BacktestResult.query.order_by(BacktestResult.created_at.desc()).limit(limit).all()

    def list_recent_summaries(self, limit: int = 30) -> list[dict[str, Any]]:
        """Lightweight rows for /backtest/ (avoids loading huge metrics_json blobs)."""
        dialect = db.session.get_bind().dialect.name
        if dialect == "mysql":
            sql = text(
                """
                SELECT br.id, br.created_at, br.period_days, br.timeframe,
                       JSON_UNQUOTE(JSON_EXTRACT(br.metrics_json, '$.return_pct')) AS return_pct,
                       JSON_UNQUOTE(JSON_EXTRACT(br.metrics_json, '$.win_rate')) AS win_rate,
                       s.name AS strategy_name, c.symbol AS coin_symbol
                FROM backtest_results br
                INNER JOIN strategies s ON s.id = br.strategy_id
                INNER JOIN coins c ON c.id = br.coin_id
                ORDER BY br.created_at DESC
                LIMIT :lim
                """
            )
        else:
            sql = text(
                """
                SELECT br.id, br.created_at, br.period_days, br.timeframe,
                       json_extract(br.metrics_json, '$.return_pct') AS return_pct,
                       json_extract(br.metrics_json, '$.win_rate') AS win_rate,
                       s.name AS strategy_name, c.symbol AS coin_symbol
                FROM backtest_results br
                INNER JOIN strategies s ON s.id = br.strategy_id
                INNER JOIN coins c ON c.id = br.coin_id
                ORDER BY br.created_at DESC
                LIMIT :lim
                """
            )
        rows = db.session.execute(sql, {"lim": limit}).mappings().all()
        summaries: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            for key in ("return_pct", "win_rate"):
                val = item.get(key)
                if val is not None and not isinstance(val, (int, float)):
                    try:
                        item[key] = float(val)
                    except (TypeError, ValueError):
                        item[key] = 0.0
            summaries.append(item)
        return summaries

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
