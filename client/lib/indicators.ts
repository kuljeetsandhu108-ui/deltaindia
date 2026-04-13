export const INDICATORS =[
  { value: 'ppo', label: 'Percentage Price Oscillator (PPO)', params:[{name: 'fast', def: 12}, {name: 'slow', def: 26}] },
  { value: 'stdev', label: 'Standard Deviation', params: [{name: 'length', def: 14}] },
  { value: 'obv', label: 'On Balance Volume (OBV)', params:[] },
  { value: 'adl', label: 'Accumulation/Distribution Line (A/D)', params:[] },
  { value: 'cmf', label: 'Chaikin Money Flow (CMF)', params: [{name: 'length', def: 20}] },
  { value: 'hma', label: 'Hull Moving Average (HMA)', params:[{name: 'length', def: 14}] },
  { value: 'williams_r', label: 'Williams %R', params:[{name: 'length', def: 14}] },
  { value: 'mom', label: 'Momentum Oscillator', params: [{name: 'length', def: 10}] },
  { value: 'tsi', label: 'True Strength Index (TSI)', params:[{name: 'long_length', def: 25}, {name: 'short_length', def: 13}] },
  { value: 'uo', label: 'Ultimate Oscillator', params:[{name: 'fast', def: 7}, {name: 'mid', def: 14}, {name: 'slow', def: 28}] },

  { value: 'supertrend', label: 'SuperTrend', params:[{name: 'length', def: 10}, {name: 'multiplier', def: 3.0}] },
  { value: 'psar', label: 'Parabolic SAR', params:[{name: 'step', def: 0.02}, {name: 'max_step', def: 0.2}] },
  { value: 'donchian_upper', label: 'Donchian Channels Upper', params:[{name: 'length', def: 20}] },
  { value: 'donchian_lower', label: 'Donchian Channels Lower', params: [{name: 'length', def: 20}] },
  { value: 'keltner_upper', label: 'Keltner Channel Upper', params:[{name: 'length', def: 20}, {name: 'multiplier', def: 2.0}] },
  { value: 'keltner_lower', label: 'Keltner Channel Lower', params:[{name: 'length', def: 20}, {name: 'multiplier', def: 2.0}] },
  { value: 'aroon_up', label: 'Aroon Up', params:[{name: 'length', def: 14}] },
  { value: 'aroon_down', label: 'Aroon Down', params:[{name: 'length', def: 14}] },

  // --- TREND ---
  { value: 'sma', label: 'SMA (Simple Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'ema', label: 'EMA (Exponential Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'wma', label: 'WMA (Weighted Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'macd', label: 'MACD Line', params: [{name: 'fast', def: 12}, {name: 'slow', def: 26}, {name: 'sig', def: 9}] },
  { value: 'vwap', label: 'VWAP (Volume Weighted Avg Price)', params: [{name: 'length', def: 14}] },
  { value: 'adx', label: 'ADX (Average Directional Index)', params: [{name: 'length', def: 14}] },
  { value: 'ichimoku_a', label: 'Ichimoku Span A', params: [] },
  { value: 'ichimoku_b', label: 'Ichimoku Span B', params: [] },

  // --- MOMENTUM ---
  { value: 'rsi', label: 'RSI (Relative Strength Index)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'stoch_k', label: 'Stochastic %K', params: [{name: 'window', def: 14}, {name: 'smooth', def: 3}] },
  { value: 'stoch_d', label: 'Stochastic %D', params: [{name: 'window', def: 14}, {name: 'smooth', def: 3}] },
  { value: 'cci', label: 'CCI', params: [{name: 'length', def: 20}] },
  { value: 'roc', label: 'Rate of Change', params: [{name: 'length', def: 12}] },

  // --- VOLATILITY ---
  { value: 'bb_upper', label: 'Bollinger Bands Upper', params: [{name: 'length', def: 20}, {name: 'std', def: 2.0}] },
  { value: 'bb_lower', label: 'Bollinger Bands Lower', params: [{name: 'length', def: 20}, {name: 'std', def: 2.0}] },
  { value: 'atr', label: 'ATR', params: [{name: 'length', def: 14}] },

  // --- RAW DATA ---
  { value: 'close', label: 'Price (Close)', params: [] },
  { value: 'open', label: 'Price (Open)', params: [] },
  { value: 'high', label: 'Price (High)', params: [] },
  { value: 'low', label: 'Price (Low)', params: [] },
  { value: 'volume', label: 'Volume', params: [] },
  { value: 'number', label: 'Fixed Number', params: [{name: 'value', def: 50}] }
];
