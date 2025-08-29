PRAGMA foreign_keys = ON;

-- Schema for AI Crypto Wallet logging and operations

-- Snapshots of balances per asset at a point in time
CREATE TABLE IF NOT EXISTS balance_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  captured_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  asset TEXT NOT NULL,              -- e.g., ETH, USDC, WBTC
  balance REAL NOT NULL,            -- native units
  usd_price REAL,                   -- optional price used
  usd_value REAL,                   -- balance * usd_price (if provided)
  source TEXT                       -- where the data came from (rpc, cache, etc)
);

CREATE INDEX IF NOT EXISTS idx_balance_snapshots_captured_at
  ON balance_snapshots (captured_at);

CREATE INDEX IF NOT EXISTS idx_balance_snapshots_asset_time
  ON balance_snapshots (asset, captured_at);

-- AI/rule-based trading suggestions
CREATE TABLE IF NOT EXISTS suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  rule TEXT NOT NULL,                  -- e.g., RSI_BUY, REBALANCE, TAKE_PROFIT
  asset_from TEXT,                     -- optional (e.g., USDC)
  asset_to TEXT,                       -- target asset (e.g., ETH)
  amount_usd REAL,                     -- suggested USD size (pre risk capping)
  confidence REAL,                     -- optional 0..1
  params_json TEXT,                    -- serialized parameters used by the rule
  reasoning TEXT                       -- human-readable explanation
);

CREATE INDEX IF NOT EXISTS idx_suggestions_created_at
  ON suggestions (created_at);

-- Manual decision taken on a suggestion (approve/reject)
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  suggestion_id INTEGER NOT NULL,
  decided_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','expired','cancelled')),
  reason TEXT,
  FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_decisions_suggestion_id
  ON decisions (suggestion_id);

-- Executed trades linked to suggestions
CREATE TABLE IF NOT EXISTS trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  suggestion_id INTEGER NOT NULL,
  executed_at DATETIME,
  status TEXT NOT NULL CHECK (status IN ('submitted','confirmed','failed','cancelled')),
  tx_hash TEXT UNIQUE,
  asset_from TEXT,
  amount_from REAL,
  asset_to TEXT,
  amount_to REAL,
  slippage_bps INTEGER,              -- slippage in basis points
  gas_est_usd REAL,
  error TEXT,
  FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trades_status_time
  ON trades (status, executed_at);

-- Simple runtime flags (e.g., emergency stop)
CREATE TABLE IF NOT EXISTS runtime_flags (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

