export const INDICATORS = [
  // --- TREND ---
  { value: 'sma', label: 'SMA (Simple Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'ema', label: 'EMA (Exponential Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'wma', label: 'WMA (Weighted Moving Average)', params: [{name: 'length', def: 14}, {name: 'source', def: 'close'}] },
  { value: 'macd', label: 'MACD Line', params: [{name: 'fast', def: 12}, {name: 'slow', def: 26}, {name: 'sig', def: 9}] },
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
