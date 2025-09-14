-- Tabela para registrar todas as operações de compra e venda
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    token_address VARCHAR(100) NOT NULL,
    token_name VARCHAR(100),
    token_symbol VARCHAR(50),
    
    -- Informações da compra
    buy_price DECIMAL(30, 10) NOT NULL,
    buy_amount DECIMAL(30, 10) NOT NULL,
    buy_transaction_hash VARCHAR(200),
    buy_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Informações da venda (NULL até ser vendido)
    sell_price DECIMAL(30, 10),
    sell_amount DECIMAL(30, 10),
    sell_transaction_hash VARCHAR(200),
    sell_time TIMESTAMP,
    sell_reason VARCHAR(50), -- 'PROFIT_TARGET', 'STOP_LOSS', 'MANUAL'
    
    -- Cálculos de performance
    profit_loss_amount DECIMAL(30, 10),
    profit_loss_percentage DECIMAL(10, 2),
    
    -- Status
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED, FAILED
    
    -- Referência à sugestão original
    suggestion_id VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para monitorar preços dos tokens em trade
CREATE TABLE IF NOT EXISTS price_monitoring (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id),
    token_address VARCHAR(100) NOT NULL,
    current_price DECIMAL(30, 10) NOT NULL,
    price_change_percentage DECIMAL(10, 2),
    monitored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configurações de trading
CREATE TABLE IF NOT EXISTS trade_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value VARCHAR(200) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir configurações padrão
INSERT INTO trade_config (config_key, config_value, description) VALUES
    ('profit_target_percentage', '20', 'Porcentagem de lucro para vender automaticamente'),
    ('stop_loss_percentage', '5', 'Porcentagem de prejuízo para vender automaticamente'),
    ('monitoring_interval_seconds', '60', 'Intervalo em segundos para monitorar preços'),
    ('max_trade_amount_sol', '0.1', 'Valor máximo em SOL para cada trade'),
    ('auto_trading_enabled', 'false', 'Se o trading automático está ativo')
ON CONFLICT (config_key) DO NOTHING;

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_trades_token_address ON trades(token_address);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_buy_time ON trades(buy_time);
CREATE INDEX IF NOT EXISTS idx_price_monitoring_trade_id ON price_monitoring(trade_id);
CREATE INDEX IF NOT EXISTS idx_price_monitoring_monitored_at ON price_monitoring(monitored_at);

-- View para trades abertos
CREATE OR REPLACE VIEW open_trades AS
SELECT 
    t.*,
    pm.current_price as last_monitored_price,
    pm.price_change_percentage as last_price_change,
    pm.monitored_at as last_monitored_at
FROM trades t
LEFT JOIN LATERAL (
    SELECT * FROM price_monitoring 
    WHERE trade_id = t.id 
    ORDER BY monitored_at DESC 
    LIMIT 1
) pm ON true
WHERE t.status = 'OPEN';

-- View para estatísticas de trading
CREATE OR REPLACE VIEW trading_stats AS
SELECT 
    COUNT(*) as total_trades,
    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
    COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades,
    COUNT(CASE WHEN profit_loss_percentage > 0 THEN 1 END) as winning_trades,
    COUNT(CASE WHEN profit_loss_percentage < 0 THEN 1 END) as losing_trades,
    AVG(CASE WHEN status = 'CLOSED' THEN profit_loss_percentage END) as avg_profit_loss_percentage,
    SUM(CASE WHEN status = 'CLOSED' THEN profit_loss_amount END) as total_profit_loss
FROM trades;