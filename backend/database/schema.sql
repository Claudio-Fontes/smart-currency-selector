-- Schema for Smart Currency Selector Database
-- Table to store suggested tokens with all details

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main table for suggested tokens
CREATE TABLE IF NOT EXISTS suggested_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_address VARCHAR(255) NOT NULL,
    token_name VARCHAR(255),
    token_symbol VARCHAR(50),
    chain VARCHAR(50) NOT NULL,
    
    -- Price metrics
    price_usd DECIMAL(20, 10),
    price_change_24h DECIMAL(10, 4),
    volume_24h DECIMAL(20, 2),
    liquidity_usd DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    
    -- Security metrics  
    pool_score INTEGER,
    liquidity_locked BOOLEAN,
    is_audited BOOLEAN,
    honeypot_risk BOOLEAN,
    
    -- Holders analysis
    holder_count INTEGER,
    top_10_holders_percentage DECIMAL(5, 2),
    concentration_risk VARCHAR(20),
    
    -- Price trend analysis
    price_trend VARCHAR(20),
    trend_confidence DECIMAL(5, 2),
    
    -- Pool information
    pool_address VARCHAR(255),
    pool_created_at TIMESTAMP,
    dex_name VARCHAR(100),
    
    -- Analysis metadata
    suggestion_reason TEXT,
    analysis_score DECIMAL(5, 2),
    risk_level VARCHAR(20),
    
    -- System metadata
    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional data as JSON for flexibility
    raw_data JSONB
);

-- Index for better query performance
CREATE INDEX IF NOT EXISTS idx_suggested_tokens_chain ON suggested_tokens(chain);
CREATE INDEX IF NOT EXISTS idx_suggested_tokens_suggested_at ON suggested_tokens(suggested_at);
CREATE INDEX IF NOT EXISTS idx_suggested_tokens_token_address ON suggested_tokens(token_address);
CREATE INDEX IF NOT EXISTS idx_suggested_tokens_analysis_score ON suggested_tokens(analysis_score);
CREATE INDEX IF NOT EXISTS idx_suggested_tokens_risk_level ON suggested_tokens(risk_level);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_suggested_tokens_updated_at 
    BEFORE UPDATE ON suggested_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();