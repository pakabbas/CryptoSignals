from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SimTrade:
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    pnl_pct: float
    duration_bars: int


def build_metrics(
    trades: list[SimTrade],
    equity_curve: list[dict[str, Any]],
    drawdown_curve: list[dict[str, Any]],
    buy_signals: int,
    sell_signals: int,
    initial_equity: float = 10_000.0,
) -> dict[str, Any]:
    total = len(trades)
    wins = [t for t in trades if t.pnl_pct > 0]
    losses = [t for t in trades if t.pnl_pct <= 0]
    win_pnls = [t.pnl_pct for t in wins]
    loss_pnls = [t.pnl_pct for t in losses]

    gross_profit = sum(win_pnls)
    gross_loss = abs(sum(loss_pnls))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit or 0.0)

    final_equity = equity_curve[-1]["equity"] if equity_curve else initial_equity
    return_pct = ((final_equity - initial_equity) / initial_equity) * 100

    max_drawdown = max((point["drawdown_pct"] for point in drawdown_curve), default=0.0)

    return {
        "total_trades": total,
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": (len(wins) / total * 100) if total else 0.0,
        "profit_pct": sum(t.pnl_pct for t in wins),
        "loss_pct": sum(t.pnl_pct for t in losses),
        "profit_factor": round(profit_factor, 4),
        "average_win": (sum(win_pnls) / len(win_pnls)) if win_pnls else 0.0,
        "average_loss": (sum(loss_pnls) / len(loss_pnls)) if loss_pnls else 0.0,
        "maximum_drawdown": round(max_drawdown, 4),
        "largest_win": max(win_pnls) if win_pnls else 0.0,
        "largest_loss": min(loss_pnls) if loss_pnls else 0.0,
        "longest_winning_streak": _longest_streak(trades, win=True),
        "longest_losing_streak": _longest_streak(trades, win=False),
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "average_trade_duration_bars": (sum(t.duration_bars for t in trades) / total) if total else 0.0,
        "return_pct": round(return_pct, 4),
        "initial_equity": initial_equity,
        "final_equity": round(final_equity, 2),
        "trades": [asdict(t) for t in trades],
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
    }


def _longest_streak(trades: list[SimTrade], *, win: bool) -> int:
    best = current = 0
    for trade in trades:
        is_win = trade.pnl_pct > 0
        if is_win == win:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best
