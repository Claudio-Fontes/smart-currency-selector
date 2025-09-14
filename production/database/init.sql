-- Smart Currency Selector Database Schema
-- This file initializes the database schema for production

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for fresh deployments)
DROP TABLE IF EXISTS price_monitoring CASCADE;
DROP TABLE IF EXISTS token_blacklist CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS suggested_tokens CASCADE;
DROP TABLE IF EXISTS trade_config CASCADE;

-- Create suggested_tokens table
CREATE TABLE suggested_tokens (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(255) NOT NULL,
    token_name VARCHAR(255),
    token_symbol VARCHAR(50),
    price_usd DECIMAL(20, 12),
    market_cap_usd DECIMAL(20, 2),
    volume_24h_usd DECIMAL(20, 2),
    analysis_score INTEGER DEFAULT 0,
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) DEFAULT 'dextools'
);

-- Create trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(255) NOT NULL,
    token_name VARCHAR(255),
    token_symbol VARCHAR(50),
    buy_price DECIMAL(20, 12) NOT NULL,
    buy_amount DECIMAL(20, 6) NOT NULL,
    buy_transaction_hash VARCHAR(255),
    buy_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sell_price DECIMAL(20, 12),
    sell_amount DECIMAL(20, 6),
    sell_transaction_hash VARCHAR(255),
    sell_time TIMESTAMP,
    sell_reason VARCHAR(50),
    profit_loss_amount DECIMAL(20, 6),
    profit_loss_percentage DECIMAL(10, 4),
    status VARCHAR(20) DEFAULT 'OPEN',
    suggestion_id INTEGER REFERENCES suggested_tokens(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create token_blacklist table
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(255) UNIQUE NOT NULL,
    token_symbol VARCHAR(50),
    reason VARCHAR(255) DEFAULT 'Stop loss triggered',
    loss_percentage DECIMAL(10, 4),
    trade_id INTEGER REFERENCES trades(id),
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create price_monitoring table
CREATE TABLE price_monitoring (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    token_address VARCHAR(255) NOT NULL,
    current_price DECIMAL(20, 12) NOT NULL,
    price_change_percentage DECIMAL(10, 4),
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create trade_config table
CREATE TABLE trade_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value VARCHAR(255) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_suggested_tokens_address ON suggested_tokens(token_address);
CREATE INDEX idx_suggested_tokens_suggested_at ON suggested_tokens(suggested_at);
CREATE INDEX idx_suggested_tokens_score ON suggested_tokens(analysis_score);

CREATE INDEX idx_trades_address ON trades(token_address);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_buy_time ON trades(buy_time);
CREATE INDEX idx_trades_sell_time ON trades(sell_time);

CREATE INDEX idx_blacklist_address ON token_blacklist(token_address);

CREATE INDEX idx_price_monitoring_trade_id ON price_monitoring(trade_id);
CREATE INDEX idx_price_monitoring_monitored_at ON price_monitoring(monitored_at);

CREATE INDEX idx_trade_config_key ON trade_config(config_key);

-- Insert default configuration
INSERT INTO trade_config (config_key, config_value, description) VALUES
    ('auto_trading_enabled', 'false', 'Enable/disable automatic trading'),
    ('max_trade_amount_sol', '0.05', 'Maximum SOL amount per trade'),
    ('profit_target_percentage', '20', 'Target profit percentage to sell'),
    ('stop_loss_percentage', '10', 'Stop loss percentage to sell'),
    ('monitoring_interval_seconds', '30', 'Monitoring interval in seconds'),
    ('max_daily_trades_per_token', '3', 'Maximum trades per token per day'),
    ('cooldown_after_profit_hours', '2', 'Hours to wait after profitable trade'),
    ('analysis_score_threshold', '80', 'Minimum analysis score to consider token')
ON CONFLICT (config_key) DO NOTHING;

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trade_config_updated_at BEFORE UPDATE ON trade_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (assuming we're using the default user)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;