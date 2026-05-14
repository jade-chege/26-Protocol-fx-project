import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import pytz
from p3_yfinance_scanner import P3Scanner

def test_p3_scanner_init():
    # Test default tickers
    scanner = P3Scanner()
    assert scanner.tickers == ["EURUSD=X", "GBPUSD=X", "GC=F"]

    # Test custom tickers
    custom_tickers = ["AAPL", "MSFT"]
    scanner = P3Scanner(tickers=custom_tickers)
    assert scanner.tickers == custom_tickers

def test_dual_regime_rsi():
    scanner = P3Scanner()

    # is_bullish = True
    # price > ema: RSI < 50
    assert scanner.dual_regime_rsi(rsi=45, is_bullish=True, price=100, ema=90) is True
    assert scanner.dual_regime_rsi(rsi=55, is_bullish=True, price=100, ema=90) is False

    # price < ema: RSI < 35
    assert scanner.dual_regime_rsi(rsi=30, is_bullish=True, price=80, ema=90) is True
    assert scanner.dual_regime_rsi(rsi=40, is_bullish=True, price=80, ema=90) is False

    # is_bullish = False
    # price < ema: RSI > 50
    assert scanner.dual_regime_rsi(rsi=55, is_bullish=False, price=80, ema=90) is True
    assert scanner.dual_regime_rsi(rsi=45, is_bullish=False, price=80, ema=90) is False

    # price > ema: RSI > 65
    assert scanner.dual_regime_rsi(rsi=70, is_bullish=False, price=100, ema=90) is True
    assert scanner.dual_regime_rsi(rsi=60, is_bullish=False, price=100, ema=90) is False

def test_calculate_indicators():
    scanner = P3Scanner()

    # Create synthetic data (need at least 200 bars for EMA200 to be meaningful,
    # but let's just check if columns are created and values are calculated)
    data = {
        'Open': np.random.randn(250) + 100,
        'High': np.random.randn(250) + 102,
        'Low': np.random.randn(250) + 98,
        'Close': np.random.randn(250) + 100,
        'Volume': np.random.randint(100, 1000, 250)
    }
    df = pd.DataFrame(data)

    result_df = scanner.calculate_indicators(df)

    expected_cols = ['EMA200', 'TR', 'ATR14', 'AvgVol20', 'RSI14', 'ADX14']
    for col in expected_cols:
        assert col in result_df.columns
        assert not result_df[col].isna().all()

@patch('yfinance.download')
def test_fetch_data(mock_download):
    # Mock return value
    dates = pd.date_range(start="2023-01-01", periods=5, freq='4h')
    mock_df = pd.DataFrame({
        'Open': [1.0, 1.1, 1.2, 1.3, 1.4],
        'High': [1.05, 1.15, 1.25, 1.35, 1.45],
        'Low': [0.95, 1.05, 1.15, 1.25, 1.35],
        'Close': [1.02, 1.12, 1.22, 1.32, 1.42],
        'Volume': [100, 110, 120, 130, 140]
    }, index=dates)

    # yfinance sometimes returns MultiIndex columns
    mock_df.columns = pd.MultiIndex.from_tuples([('Open', 'EURUSD=X'), ('High', 'EURUSD=X'), ('Low', 'EURUSD=X'), ('Close', 'EURUSD=X'), ('Volume', 'EURUSD=X')])

    mock_download.return_value = mock_df

    scanner = P3Scanner()
    df = scanner.fetch_data("EURUSD=X")

    assert not df.empty
    assert df.index.tz.zone == 'Europe/London'
    assert isinstance(df.columns, pd.Index)
    assert not isinstance(df.columns, pd.MultiIndex)

def test_detect_patterns_hammer():
    scanner = P3Scanner()

    # Create a synthetic dataframe for a Hammer
    # Hammer: Lower wick >= 2x body, Upper wick < 0.5x body
    # Context: Bullish context (dual_regime_rsi), Close > EMA200, range > ATR

    dates = pd.date_range(start="2023-01-01 12:00", periods=3, freq='4h', tz='Europe/London')

    df = pd.DataFrame({
        'Open': [100, 100, 105],
        'High': [105, 100.2, 110],
        'Low': [95, 95, 104],
        'Close': [100, 99, 108],
        'Volume': [100, 100, 100],
        'EMA200': [90, 90, 90],
        'ATR14': [2, 2, 2],
        'RSI14': [40, 40, 40] # RSI < 50 and price > EMA200 is bullish context
    }, index=dates)

    # Bar 1: Hammer
    # body = 100 - 99 = 1
    # wick_lower = 99 - 95 = 4 (>= 2 * body)
    # wick_upper = 100.2 - 100 = 0.2 (< 0.5 * body)
    # range = 100.2 - 95 = 5.2 (> ATR 2)
    # price 99 > EMA 90
    # Confirmed by Bar 2: Close 108 > High 100.2

    result = scanner.detect_patterns(df)

    hammer_row = result.iloc[1]
    assert hammer_row['Pattern'] == 'Hammer'
    assert hammer_row['Signal'] == 'Bullish'
    assert hammer_row['Confirmed'] is True

def test_detect_patterns_shooting_star():
    scanner = P3Scanner()

    dates = pd.date_range(start="2023-01-01 12:00", periods=3, freq='4h', tz='Europe/London')

    df = pd.DataFrame({
        'Open': [100, 100, 95],
        'High': [105, 105, 96],
        'Low': [95, 99.8, 90],
        'Close': [100, 101, 92],
        'Volume': [100, 100, 100],
        'EMA200': [110, 110, 110],
        'ATR14': [2, 2, 2],
        'RSI14': [60, 60, 60] # RSI > 50 and price < EMA200 is bearish context
    }, index=dates)

    # Bar 1: Shooting Star
    # body = 101 - 100 = 1
    # wick_upper = 105 - 101 = 4 (>= 2 * body)
    # wick_lower = 100 - 99.8 = 0.2 (< 0.5 * body)
    # range = 105 - 99.8 = 5.2 (> ATR 2)
    # price 101 < EMA 110
    # Confirmed by Bar 2: Close 92 < Low 99.8

    result = scanner.detect_patterns(df)

    ss_row = result.iloc[1]
    assert ss_row['Pattern'] == 'Shooting Star'
    assert ss_row['Signal'] == 'Bearish'
    assert ss_row['Confirmed'] is True

def test_detect_patterns_bearish_engulfing():
    scanner = P3Scanner()

    dates = pd.date_range(start="2023-01-01 12:00", periods=3, freq='4h', tz='Europe/London')

    df = pd.DataFrame({
        'Open': [100, 105, 95],
        'High': [106, 106, 96],
        'Low': [99, 94, 90],
        'Close': [105, 94, 92],
        'Volume': [100, 100, 100],
        'EMA200': [110, 110, 110],
        'ATR14': [2, 2, 2],
        'RSI14': [60, 60, 60]
    }, index=dates)

    # Bar 0: Bullish (100 -> 105)
    # Bar 1: Bearish Engulfing (105 -> 94)
    # Close(1) 94 < Open(0) 100 AND Open(1) 105 >= Close(0) 105
    # Confirmed by Bar 2: Close 92 < Low 94

    result = scanner.detect_patterns(df)

    be_row = result.iloc[1]
    assert be_row['Pattern'] == 'Bearish Engulfing'
    assert be_row['Signal'] == 'Bearish'
    assert be_row['Confirmed'] is True

def test_detect_patterns_bullish_engulfing():
    scanner = P3Scanner()

    dates = pd.date_range(start="2023-01-01 12:00", periods=3, freq='4h', tz='Europe/London')

    df = pd.DataFrame({
        'Open': [100, 95, 106],
        'High': [101, 106, 107],
        'Low': [94, 94, 105],
        'Close': [95, 106, 106.5],
        'Volume': [100, 100, 100],
        'EMA200': [90, 90, 90],
        'ATR14': [2, 2, 2],
        'RSI14': [25, 25, 25] # Strict RSI < 30
    }, index=dates)

    # Bar 0: Bearish (100 -> 95)
    # Bar 1: Bullish Engulfing (95 -> 106)
    # Close(1) 106 > Open(0) 100 AND Open(1) 95 <= Close(0) 95
    # Confirmed by Bar 2: Close 106.5 > High 106

    result = scanner.detect_patterns(df)

    bullish_engulfing_row = result.iloc[1]
    assert bullish_engulfing_row['Pattern'] == 'Bullish Engulfing'
    assert bullish_engulfing_row['Signal'] == 'Bullish'
    assert bullish_engulfing_row['Confirmed'] is True

def test_detect_patterns_invalid_session():
    scanner = P3Scanner()

    # 2:00 AM is invalid session (not 8-20)
    dates = pd.date_range(start="2023-01-01 02:00", periods=2, freq='4h', tz='Europe/London')

    df = pd.DataFrame({
        'Open': [100, 100],
        'High': [105, 100.2],
        'Low': [95, 95],
        'Close': [100, 99],
        'Volume': [100, 100],
        'EMA200': [90, 90],
        'ATR14': [2, 2],
        'RSI14': [40, 40]
    }, index=dates)

    result = scanner.detect_patterns(df)
    assert result.iloc[1]['Pattern'] is None
