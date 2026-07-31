"""Technical indicator calculations (pandas, no TA-Lib)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

IndicatorFn = Callable[[pd.DataFrame, dict[str, Any]], pd.DataFrame]


def _length(params: dict[str, Any], default: int = 14) -> int:
    return int(params.get("length", default))


def _numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("open", "high", "low", "close", "volume"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    return out


def _float_series(series: pd.Series) -> pd.Series:
    """Coerce to float64; never leave object/pd.NA dtypes that break rolling."""
    return pd.to_numeric(series, errors="coerce").astype("float64")


def _safe_div(numer: pd.Series, denom: pd.Series) -> pd.Series:
    """Divide with zero → NaN, keeping float64 (avoid pd.NA → object dtype)."""
    numer = _float_series(numer)
    denom = _float_series(denom).replace(0.0, np.nan)
    return numer / denom


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    high = _float_series(high)
    low = _float_series(low)
    prev_close = _float_series(close).shift(1)
    return pd.Series(
        np.maximum.reduce(
            [
                (high - low).to_numpy(),
                (high - prev_close).abs().to_numpy(),
                (low - prev_close).abs().to_numpy(),
            ]
        ),
        index=high.index,
        dtype="float64",
    )


def _ema_series(series: pd.Series, length: int) -> pd.Series:
    return _float_series(series).ewm(span=length, adjust=False).mean()


def _rsi_series(close: pd.Series, length: int) -> pd.Series:
    close = _float_series(close)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = _safe_div(avg_gain, avg_loss)
    return _float_series(100 - (100 / (1 + rs)))

@dataclass
class IndicatorRegistry:
    """Register and apply indicators without changing call sites."""

    def __init__(self) -> None:
        self._computers: dict[str, IndicatorFn] = {}
        self._register_builtins()

    def register(self, name: str, fn: IndicatorFn) -> None:
        self._computers[name.upper()] = fn

    def compute(self, name: str, df: pd.DataFrame, params: dict[str, Any] | None = None) -> pd.DataFrame:
        key = name.upper()
        if key not in self._computers:
            raise KeyError(f"Unknown indicator: {name}")
        params = params or {}
        return self._computers[key](_numeric_frame(df), params)

    def names(self) -> list[str]:
        return sorted(self._computers.keys())

    def _register_builtins(self) -> None:
        self.register("EMA", self._ema)
        self.register("SMA", self._sma)
        self.register("RSI", self._rsi)
        self.register("MACD", self._macd)
        self.register("BB", self._bb)
        self.register("BOLLINGER", self._bb)
        self.register("ATR", self._atr)
        self.register("CCI", self._cci)
        self.register("MFI", self._mfi)
        self.register("OBV", self._obv)
        self.register("VWAP", self._vwap)
        self.register("SUPERTREND", self._supertrend)
        self.register("STOCHRSI", self._stochrsi)
        self.register("KELTNER", self._keltner)
        self.register("DONCHIAN", self._donchian)
        self.register("ADX", self._adx)
        self.register("ICHIMOKU", self._ichimoku)

    @staticmethod
    def _adx(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 14)
        out = df.copy()
        high = _float_series(out["high"])
        low = _float_series(out["low"])
        up = high.diff()
        down = -low.diff()
        plus_dm = up.where((up > down) & (up > 0), 0.0)
        minus_dm = down.where((down > up) & (down > 0), 0.0)
        tr = _true_range(high, low, out["close"])
        atr = tr.rolling(length).mean()
        plus_di = 100 * _safe_div(plus_dm.rolling(length).mean(), atr)
        minus_di = 100 * _safe_div(minus_dm.rolling(length).mean(), atr)
        dx = 100 * _safe_div((plus_di - minus_di).abs(), plus_di + minus_di)
        out[f"ADX_{length}"] = _float_series(dx).rolling(length).mean()
        return out

    @staticmethod
    def _ichimoku(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        out = df.copy()
        high = _float_series(out["high"])
        low = _float_series(out["low"])
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        span_a = ((tenkan + kijun) / 2).shift(26)
        span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        cloud_top = np.maximum(span_a.to_numpy(dtype="float64"), span_b.to_numpy(dtype="float64"))
        cloud_bottom = np.minimum(span_a.to_numpy(dtype="float64"), span_b.to_numpy(dtype="float64"))
        out["ICHI_tenkan"] = tenkan
        out["ICHI_kijun"] = kijun
        out["ICHI_cloud_top"] = cloud_top
        out["ICHI_cloud_bottom"] = cloud_bottom
        return out
    @staticmethod
    def _ema(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        out = df.copy()
        out[f"EMA_{length}"] = _ema_series(out["close"], length)
        return out

    @staticmethod
    def _sma(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        source = params.get("source", "close")
        out = df.copy()
        series = out["volume"] if source == "volume" else out["close"]
        out[f"SMA_{source}_{length}"] = _float_series(series).rolling(length).mean()
        return out
    @staticmethod
    def _rsi(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 14)
        out = df.copy()
        out[f"RSI_{length}"] = _rsi_series(out["close"], length)
        return out

    @staticmethod
    def _macd(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
        out = df.copy()
        ema_fast = _ema_series(out["close"], fast)
        ema_slow = _ema_series(out["close"], slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        out[f"MACD_{fast}_{slow}_{signal}"] = macd_line
        out[f"MACDs_{fast}_{slow}_{signal}"] = signal_line
        out[f"MACDh_{fast}_{slow}_{signal}"] = macd_line - signal_line
        return out

    @staticmethod
    def _bb(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        std = float(params.get("std", 2.0))
        out = df.copy()
        mid = out["close"].rolling(length).mean()
        dev = out["close"].rolling(length).std()
        out[f"BBM_{length}_{std}"] = mid
        out[f"BBU_{length}_{std}"] = mid + std * dev
        out[f"BBL_{length}_{std}"] = mid - std * dev
        return out

    @staticmethod
    def _atr(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 14)
        out = df.copy()
        tr = _true_range(out["high"], out["low"], out["close"])
        out[f"ATR_{length}"] = tr.rolling(length).mean()
        return out
    @staticmethod
    def _cci(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        out = df.copy()
        tp = (out["high"] + out["low"] + out["close"]) / 3
        sma = tp.rolling(length).mean()
        mad = tp.rolling(length).apply(lambda x: (x - x.mean()).abs().mean(), raw=False)
        out[f"CCI_{length}"] = (tp - sma) / (0.015 * mad)
        return out

    @staticmethod
    def _mfi(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 14)
        out = df.copy()
        tp = (out["high"] + out["low"] + out["close"]) / 3
        rmf = tp * out["volume"]
        delta = tp.diff()
        pos = rmf.where(delta > 0, 0.0).rolling(length).sum()
        neg = rmf.where(delta < 0, 0.0).rolling(length).sum()
        out[f"MFI_{length}"] = 100 - (100 / (1 + _safe_div(pos, neg)))
        return out

    @staticmethod
    def _obv(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        out = df.copy()
        direction = out["close"].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        out["OBV"] = (direction * out["volume"]).fillna(0).cumsum()
        return out

    @staticmethod
    def _stochrsi(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        rsi_len = int(params.get("length", params.get("rsi_length", 14)))
        stoch_len = int(params.get("stoch_length", rsi_len))
        smooth_k = int(params.get("smooth_k", 3))
        smooth_d = int(params.get("smooth_d", 3))
        out = IndicatorRegistry._rsi(df, {"length": rsi_len})
        rsi_col = f"RSI_{rsi_len}"
        rsi = _float_series(out[rsi_col])
        min_rsi = rsi.rolling(stoch_len).min()
        max_rsi = rsi.rolling(stoch_len).max()
        raw_k = _safe_div(rsi - min_rsi, max_rsi - min_rsi)
        # Scale 0–100 to match common StochRSI thresholds (20/80).
        raw_k = raw_k * 100
        k = raw_k.rolling(smooth_k).mean()
        d = k.rolling(smooth_d).mean()
        suffix = f"{rsi_len}_{stoch_len}_{smooth_k}_{smooth_d}"
        out[f"STOCHRSIk_{suffix}"] = k
        out[f"STOCHRSId_{suffix}"] = d
        # Backward-compatible alias used by older specs
        out[f"STOCHRSIk_{rsi_len}"] = k
        return out

    @staticmethod
    def _vwap(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        """Session VWAP resetting each UTC day (ScalpingResearch standard)."""
        out = df.copy()
        tp = (out["high"] + out["low"] + out["close"]) / 3
        typical_vol = tp * out["volume"]
        if isinstance(out.index, pd.DatetimeIndex):
            day = out.index.tz_convert("UTC").date if out.index.tz is not None else out.index.date
            day_key = pd.Series(day, index=out.index)
            cum_pv = typical_vol.groupby(day_key).cumsum()
            cum_vol = out["volume"].groupby(day_key).cumsum()
            out["VWAP"] = _safe_div(cum_pv, cum_vol)
        else:
            out["VWAP"] = _safe_div(typical_vol.cumsum(), out["volume"].cumsum())
        return out

    @staticmethod
    def _supertrend(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 10)
        multiplier = float(params.get("multiplier", 3.0))
        out = IndicatorRegistry._atr(df, {"length": length})
        atr_col = f"ATR_{length}"
        hl2 = (out["high"] + out["low"]) / 2
        upper = hl2 + multiplier * out[atr_col]
        lower = hl2 - multiplier * out[atr_col]
        out[f"SUPERTd_{length}"] = lower
        out[f"SUPERTu_{length}"] = upper
        return out

    @staticmethod
    def _keltner(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        mult = float(params.get("mult", 2.0))
        out = IndicatorRegistry._ema(df, {"length": length})
        out = IndicatorRegistry._atr(out, {"length": length})
        mid = out[f"EMA_{length}"]
        atr = out[f"ATR_{length}"]
        out[f"KCBe_{length}"] = mid
        out[f"KCUe_{length}"] = mid + mult * atr
        out[f"KCLe_{length}"] = mid - mult * atr
        return out

    @staticmethod
    def _donchian(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        length = _length(params, 20)
        out = df.copy()
        out[f"DCL_{length}"] = out["low"].rolling(length).min()
        out[f"DCU_{length}"] = out["high"].rolling(length).max()
        out[f"DCM_{length}"] = (out[f"DCL_{length}"] + out[f"DCU_{length}"]) / 2
        return out


default_registry = IndicatorRegistry()
