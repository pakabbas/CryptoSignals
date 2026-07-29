"""Technical indicator calculations (pandas, no TA-Lib)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

IndicatorFn = Callable[[pd.DataFrame, dict[str, Any]], pd.DataFrame]


def _length(params: dict[str, Any], default: int = 14) -> int:
    return int(params.get("length", default))


def _ema_series(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rsi_series(close: pd.Series, length: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


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
        return self._computers[key](df, params)

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
        up = out["high"].diff()
        down = -out["low"].diff()
        plus_dm = up.where((up > down) & (up > 0), 0.0)
        minus_dm = down.where((down > up) & (down > 0), 0.0)
        prev_close = out["close"].shift(1)
        tr = pd.concat(
            [
                out["high"] - out["low"],
                (out["high"] - prev_close).abs(),
                (out["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(length).mean()
        plus_di = 100 * (plus_dm.rolling(length).mean() / atr.replace(0, pd.NA))
        minus_di = 100 * (minus_dm.rolling(length).mean() / atr.replace(0, pd.NA))
        dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA))
        out[f"ADX_{length}"] = dx.rolling(length).mean()
        return out

    @staticmethod
    def _ichimoku(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
        out = df.copy()
        high = out["high"]
        low = out["low"]
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        span_a = ((tenkan + kijun) / 2).shift(26)
        span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        cloud_top = pd.concat([span_a, span_b], axis=1).max(axis=1)
        cloud_bottom = pd.concat([span_a, span_b], axis=1).min(axis=1)
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
        out[f"SMA_{source}_{length}"] = series.rolling(length).mean()
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
        prev_close = out["close"].shift(1)
        tr = pd.concat(
            [
                out["high"] - out["low"],
                (out["high"] - prev_close).abs(),
                (out["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
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
        out[f"MFI_{length}"] = 100 - (100 / (1 + pos / neg.replace(0, pd.NA)))
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
        rsi = out[rsi_col]
        min_rsi = rsi.rolling(stoch_len).min()
        max_rsi = rsi.rolling(stoch_len).max()
        raw_k = (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, pd.NA)
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
        out = df.copy()
        tp = (out["high"] + out["low"] + out["close"]) / 3
        out["VWAP"] = (tp * out["volume"]).cumsum() / out["volume"].cumsum().replace(0, pd.NA)
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
