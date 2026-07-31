"""Shared scalp trade-management helpers (mandatory ScalpingResearch rules)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.risk.levels import levels_from_atr, risk_spec_from_definition


def management_from_definition(definition: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(definition, dict):
        return {}
    raw = definition.get("management")
    return dict(raw) if isinstance(raw, dict) else {}


def atr_column(df: pd.DataFrame, length: int = 14) -> str | None:
    col = f"ATR_{length}"
    return col if col in df.columns else next((c for c in df.columns if c.startswith("ATR_")), None)


def bb_mid_column(df: pd.DataFrame) -> str | None:
    return next((c for c in df.columns if c.startswith("BBM_")), None)


def bb_lower_column(df: pd.DataFrame) -> str | None:
    return next((c for c in df.columns if c.startswith("BBL_")), None)


def bb_upper_column(df: pd.DataFrame) -> str | None:
    return next((c for c in df.columns if c.startswith("BBU_")), None)


def macd_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    macd = next(
        (
            c
            for c in df.columns
            if c.startswith("MACD_") and not c.startswith("MACDh") and not c.startswith("MACDs")
        ),
        None,
    )
    signal = next((c for c in df.columns if c.startswith("MACDs_")), None)
    return macd, signal


def is_fresh_bb_touch(df: pd.DataFrame, bar_idx: int, side: str) -> bool:
    """Require prior bar closed inside bands (avoid clustered outer-band chop)."""
    if bar_idx < 1:
        return False
    lower = bb_lower_column(df)
    upper = bb_upper_column(df)
    if not lower or not upper:
        return True
    prev_close = float(df["close"].iloc[bar_idx - 1])
    prev_lo = float(df[lower].iloc[bar_idx - 1])
    prev_hi = float(df[upper].iloc[bar_idx - 1])
    return prev_lo < prev_close < prev_hi


def build_risk_levels(
    signal_type: str,
    entry: float,
    df: pd.DataFrame,
    definition: dict[str, Any],
    atr_bar_idx: int,
) -> tuple[float | None, float | None]:
    spec = risk_spec_from_definition(definition)
    if spec is None:
        return None, None
    atr_col = atr_column(df, spec.atr_length)
    if atr_col is None or atr_bar_idx < 0 or atr_bar_idx >= len(df):
        return None, None
    atr_val = df[atr_col].iloc[atr_bar_idx]
    if pd.isna(atr_val) or float(atr_val) <= 0:
        return None, None
    levels = levels_from_atr(signal_type, entry, float(atr_val), spec)
    # Template C: mandatory TP is mid-BB when available
    mgmt = management_from_definition(definition)
    if mgmt.get("exit_mid_bb"):
        mid = bb_mid_column(df)
        if mid and atr_bar_idx < len(df) and not pd.isna(df[mid].iloc[atr_bar_idx]):
            mid_px = float(df[mid].iloc[atr_bar_idx])
            if levels.side == "long" and mid_px > entry:
                return levels.stop_loss, mid_px
            if levels.side == "short" and mid_px < entry:
                return levels.stop_loss, mid_px
    return levels.stop_loss, levels.take_profit


def check_intrabar_exit(
    side: str,
    high: float,
    low: float,
    stop: float | None,
    take: float | None,
) -> tuple[str | None, float | None]:
    """Conservative: if SL and TP both touchable in same bar, take SL."""
    if side == "long":
        hit_sl = stop is not None and low <= stop
        hit_tp = take is not None and high >= take
        if hit_sl and hit_tp:
            return "sl", stop
        if hit_sl:
            return "sl", stop
        if hit_tp:
            return "tp", take
    else:
        hit_sl = stop is not None and high >= stop
        hit_tp = take is not None and low <= take
        if hit_sl and hit_tp:
            return "sl", stop
        if hit_sl:
            return "sl", stop
        if hit_tp:
            return "tp", take
    return None, None


def check_management_exit(
    *,
    side: str,
    df: pd.DataFrame,
    bar_idx: int,
    entry_index: int,
    entry_price: float,
    definition: dict[str, Any],
) -> tuple[str | None, float | None]:
    mgmt = management_from_definition(definition)
    close = float(df["close"].iloc[bar_idx])
    bars_held = bar_idx - entry_index

    # Mid-BB touch (Template C)
    if mgmt.get("exit_mid_bb"):
        mid = bb_mid_column(df)
        if mid and not pd.isna(df[mid].iloc[bar_idx]):
            mid_px = float(df[mid].iloc[bar_idx])
            high = float(df["high"].iloc[bar_idx])
            low = float(df["low"].iloc[bar_idx])
            if side == "long" and low <= mid_px <= high and mid_px > entry_price:
                return "mid_bb", mid_px
            if side == "short" and low <= mid_px <= high and mid_px < entry_price:
                return "mid_bb", mid_px

    # VWAP crossback (Template B)
    if mgmt.get("exit_vwap_crossback") and "VWAP" in df.columns and not pd.isna(df["VWAP"].iloc[bar_idx]):
        vwap = float(df["VWAP"].iloc[bar_idx])
        if side == "long" and close < vwap:
            return "vwap_crossback", close
        if side == "short" and close > vwap:
            return "vwap_crossback", close

    # MACD flip (Template B)
    if mgmt.get("exit_macd_flip") and bar_idx >= 1:
        macd_col, sig_col = macd_columns(df)
        if macd_col and sig_col:
            prev = float(df[macd_col].iloc[bar_idx - 1]) - float(df[sig_col].iloc[bar_idx - 1])
            curr = float(df[macd_col].iloc[bar_idx]) - float(df[sig_col].iloc[bar_idx])
            if side == "long" and prev >= 0 > curr:
                return "macd_flip", close
            if side == "short" and prev <= 0 < curr:
                return "macd_flip", close

    # RSI extreme exit (Template A)
    rsi_cfg = mgmt.get("exit_rsi_extreme")
    if isinstance(rsi_cfg, dict):
        length = int(rsi_cfg.get("length", 5))
        col = f"RSI_{length}"
        if col in df.columns and not pd.isna(df[col].iloc[bar_idx]):
            rsi = float(df[col].iloc[bar_idx])
            if side == "long" and rsi > float(rsi_cfg.get("long_gt", 70)):
                return "rsi_extreme", close
            if side == "short" and rsi < float(rsi_cfg.get("short_lt", 30)):
                return "rsi_extreme", close

    max_hold = int(mgmt.get("max_hold_bars") or 0)
    if max_hold > 0 and bars_held >= max_hold:
        only_losing = bool(mgmt.get("max_hold_if_losing"))
        if side == "long":
            losing = close < entry_price
        else:
            losing = close > entry_price
        if not only_losing or losing:
            return "max_hold", close

    return None, None
