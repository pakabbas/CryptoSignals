Here's what actually holds up in backtests, not recycled "RSI 30/70" folklore.

One framework runs through all four, just re-tuned per timeframe: trend filter (EMA) → regime gate (ADX) → momentum trigger (RSI/StochRSI) → confirmation (volume/MACD) → ATR-based risk. The one thing that flips as the timeframe grows: on 15m/30m you want ADX low (calm enough for mean-reversion to work), on 1h/4h you want ADX high (confirms an actual trend worth riding). Regime is the single biggest lever in what I found — the exact same Bollinger mean-reversion rule set on BTC/USDT 4h swung from a 1.62 profit factor when ADX was under 20 to a -0.74 profit factor when ADX was above 30. Get the regime wrong and any of these bleeds money. 
Vantixs

All stops/targets below use ATR, not fixed %, so they auto-scale across BTC/ETH/SOL/DOGE without separate tuning per coin — more on that in the coin notes.

1. 15m — Filtered Mean-Reversion

Hardest timeframe to find edge on. A plain RSI(14) oversold-bounce backtested on BTC 15m over 6 months had a 66.3% win rate but still lost 16.88% net across 92 trades, because it kept buying oversold dips inside a bigger downtrend. Separately, a large backtest testing one breakout-style indicator across 414 parameter combinations at 15m found only 6 configurations were actually profitable — most naive setups don't clear costs at this speed, including a 0.1% round-trip cost from taker fees alone before slippage. So keep this one selective. 
Coinquant + 2

Indicator	Setting	Role
EMA	50	Trend bias
ADX	14	Regime gate
Stochastic RSI	10,10,3,3	Entry trigger
Volume	vs 20-period avg	Confirms it's not noise
ATR	14	Stop/target sizing

Long — all of:

Price above EMA(50)
ADX(14) < 25 (not fighting a strong downtrend)
StochRSI %K crosses above %D from below 20
Candle volume ≥ 20-period average

Short — all of:

Price below EMA(50)
ADX(14) < 25
StochRSI %K crosses below %D from above 80
Candle volume ≥ 20-period average

Risk: stop = 1×ATR(14) from entry, target = 2×ATR(14).

2. 30m — Trend + Momentum Confirmation

This is roughly where edge starts showing up consistently — a large multi-instrument backtest found 30-minute and 1-hour timeframes consistently produced the most profitable results of the intraday set. MACD's stock 12/26/9 settings are fine here — retuning them for the 30-minute chart didn't produce a statistically meaningful improvement in testing. 
EXCAVO
Forex Education

Indicator	Setting	Role
EMA	21 & 50	Trend pair
MACD	12, 26, 9	Momentum confirmation
RSI	14	Avoid chasing extremes
ADX	14	Require ≥ 20
Volume	vs 20-period avg	Confirms
ATR	14	Stop/target

Long — all of:

EMA(21) above EMA(50)
MACD line crosses above signal line
RSI(14) between 45–65
ADX(14) ≥ 20
Volume ≥ 20-period average

Short — all of:

EMA(21) below EMA(50)
MACD line crosses below signal line
RSI(14) between 35–55
ADX(14) ≥ 20
Volume ≥ 20-period average

Risk: stop = 1.2×ATR(14), target = 2×stop.

3. 1h — Trend-Aligned Momentum

Best-evidenced timeframe I found. A community-published TradingView system built specifically for DOGE/USDT 1h — StochRSI + EMA trend filter + VWAP — reported 56–64% win rates and a 1.32–1.70 profit factor across 1-year, 2-year, and recent 3-month backtest windows (self-reported, worth verifying yourself, but a useful data point). The same skeleton shows up independently in a script built around an EMA(9)/(21) crossover combined with an RSI filter and ADX strength confirmation at this exact timeframe. 
tradingview
TradingView

Indicator	Setting	Role
EMA	9 & 21	Entry trigger
EMA	50	Broader trend filter
RSI	14	> 55 long / < 45 short
ADX	14	> 20
VWAP (optional)	session-anchored	Extra directional filter
ATR	14	Stop/target

Long — all of:

EMA(9) crosses above EMA(21)
Price above EMA(50)
RSI(14) > 55
ADX(14) > 20
(optional — recommended for DOGE/SOL): price above VWAP

Short — all of:

EMA(9) crosses below EMA(21)
Price below EMA(50)
RSI(14) < 45
ADX(14) > 20
(optional): price below VWAP

Risk: stop = 1.5×ATR(14), target = 2×stop.

One more thing worth knowing: the EMA-crossover research consistently warns that crossover signals get noisy below the 1h mark, and that lower-timeframe trades should only be taken in the direction of the higher-timeframe trend. If your bot already pulls more than one timeframe per coin, gating this template on the 4h trend direction is a cheap upgrade. 
altFINS

4. 4h — Trend-Following Swing

4h flips the philosophy. In a multi-asset backtest spanning BTC, ETH, gold, and major forex pairs from 2020–2025, trend-following approaches (EMA, ADX) consistently outperformed mean-reversion (RSI), and 4h is where a StochRSI+EMA+ADX stack produced the cleanest numbers I found: combined with a 50 EMA trend filter, this approach produced 55-60% win rates on 4H BTC charts, with an ADX(14) above 20 filter lifting win rate from 52% to 57% and profit factor from 1.3 to 1.6. 
Quant Signals + 2

Indicator	Setting	Role
EMA	50 & 200	Major trend structure
ADX	14	≥ 25 required
Stochastic RSI	14,14,5,5	Pullback timing
MACD	12, 26, 9	Optional confirmation
ATR	14	Stop/target

Long — all of:

EMA(50) above EMA(200)
ADX(14) ≥ 25
StochRSI %K crosses above %D from below 20 (a dip inside the uptrend, not a bottom call)
(optional): MACD line crosses above signal line

Short — all of:

EMA(50) below EMA(200)
ADX(14) ≥ 25
StochRSI %K crosses below %D from above 80
(optional): MACD line crosses below signal line

Risk: stop = 2×ATR(14), target = 2×stop minimum — let winners run further here since signals are rarer and trends more sustained. A Bollinger-squeeze breakout variant on this same timeframe has shown win rates of 55-65% with exceptional 3:1 to 6:1 reward-to-risk on the strongest setups, if you want a second 4h pattern later. 
Quantum-algo

Coin-specific notes
SOL runs roughly twice Bitcoin's realized volatility — the ATR-based stops above scale for that automatically, but it also means the 4h trend template tends to suit SOL well, since its trends run further once established. 
CME Group
DOGE is the outlier: 24-hour moves past 20% aren't unusual, and it's driven more by social/news sentiment spikes than the other three, and altcoins generally carry noticeably thinner order-book depth than BTC and ETH. Be strict about the volume filter on DOGE specifically, and lean toward 1h/4h over 15m/30m for it — the one real backtested DOGE-specific system above runs on 1h, not lower. 
Blockchain News
fxstreet
BTC/ETH are what most of this data was actually backtested on, so treat them as the reference case these parameters are most directly validated against.
Before you wire these in
Bollinger Bands + RSI + MACD is worth adding as a 5th variant in your playground — one backtest found that adding an RSI below 30 confirmation to a plain BB strategy lifted its profit factor from 1.15 to 1.52, and layering in an ADX filter pushed it to 1.89. 
Stratbase
Test each template over a longer window than 7 days before trusting it. The same 7 days gives you ~672 15m candles but only ~42 4h candles — nowhere near enough for the 4h template to mean anything. Aim for several months spanning a trend, a chop, and a drawdown, since results are this regime-dependent.
Fees bite hardest on 15m/30m given trade frequency — in two backtests measuring actual fee drag, a Bollinger Squeeze strategy lost 24% of its gross profit to fees, and a MACD Cross strategy lost 13%. Worth modeling real fees in your playground, not just win/loss counts. 
PRUVIQ
None of this is financial advice, and backtested performance describes the past, not the future — a parameter set that worked in 2023–2025 can stop working when the regime shifts. Forward-test or paper-trade before pointing any of these at real capital.

