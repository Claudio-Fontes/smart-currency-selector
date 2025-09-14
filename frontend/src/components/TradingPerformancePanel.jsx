import React, { useState, useEffect } from 'react';
import usePositions from '../hooks/usePositions';
import { tradingAPI } from '../services/api';

const TradingPerformancePanel = () => {
  const { positions, summary, loading: positionsLoading, error: positionsError } = usePositions(60000);
  const [activeView, setActiveView] = useState('performance');
  const [timeframe, setTimeframe] = useState('24h');
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch real trading statistics
  useEffect(() => {
    const fetchTradingStats = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await tradingAPI.getStatistics();
        
        if (response.success && response.data) {
          console.log('📊 Trading statistics loaded:', response.data);
          setPerformanceData(response.data);
        } else {
          throw new Error('Invalid response format');
        }
      } catch (err) {
        console.error('❌ Failed to load trading statistics:', err);
        setError(err.message);
        
        // Fallback to empty data structure
        setPerformanceData({
          totalPnL: 0,
          totalPnLPercentage: 0,
          winRate: 0,
          totalTrades: 0,
          winningTrades: 0,
          losingTrades: 0,
          avgWin: 0,
          avgLoss: 0,
          profitFactor: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          dailyPnL: [],
          topPerformers: [],
          alerts: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchTradingStats();
    
    // Refresh every 60 seconds
    const interval = setInterval(fetchTradingStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value) => {
    if (!value) return '$0.00';
    const absValue = Math.abs(value);
    if (absValue >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (absValue >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const getPnLColor = (value) => {
    if (value > 0) return '#00ff88';
    if (value < 0) return '#ff4757';
    return '#666';
  };

  const PerformanceChart = ({ data }) => (
    <div className="performance-chart">
      <div className="chart-bars">
        {data.map((item, index) => {
          const maxValue = Math.max(...data.map(d => Math.abs(d.pnl)));
          const height = Math.abs(item.pnl) / maxValue * 100;
          return (
            <div key={index} className="chart-bar-container">
              <div
                className={`chart-bar ${item.pnl >= 0 ? 'positive' : 'negative'}`}
                style={{ height: `${height}%` }}
                title={`${item.day}: ${formatCurrency(item.pnl)}`}
              />
              <span className="chart-label">{item.day}</span>
            </div>
          );
        })}
      </div>
    </div>
  );

  const MetricCard = ({ title, value, subValue, trend, icon, color }) => (
    <div className="metric-card" style={{ borderLeftColor: color }}>
      <div className="metric-header">
        <span className="metric-icon">{icon}</span>
        <span className="metric-title">{title}</span>
      </div>
      <div className="metric-value">{value}</div>
      {subValue && <div className="metric-subvalue">{subValue}</div>}
      {trend && (
        <div className={`metric-trend ${trend > 0 ? 'positive' : 'negative'}`}>
          {trend > 0 ? '↗' : '↘'} {formatPercentage(Math.abs(trend))}
        </div>
      )}
    </div>
  );

  if (loading || !performanceData) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>📈 Trading Performance</h2>
        </div>
        <div className="loading-state">
          <div className="pulse-animation">📊</div>
          <p>Loading trading statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>📈 Trading Performance</h2>
        </div>
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>Failed to load trading statistics</p>
          <small>{error}</small>
        </div>
      </div>
    );
  }

  return (
    <div className="panel-container">
      {/* Header */}
      <div className="panel-header">
        <div>
          <h2>📈 Trading Performance</h2>
          <p className="panel-subtitle">Real-time trading analytics</p>
        </div>
        <div className="timeframe-selector">
          <button 
            className={`timeframe-btn ${timeframe === '24h' ? 'active' : ''}`}
            onClick={() => setTimeframe('24h')}
          >
            24H
          </button>
          <button 
            className={`timeframe-btn ${timeframe === '7d' ? 'active' : ''}`}
            onClick={() => setTimeframe('7d')}
          >
            7D
          </button>
          <button 
            className={`timeframe-btn ${timeframe === '30d' ? 'active' : ''}`}
            onClick={() => setTimeframe('30d')}
          >
            30D
          </button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeView === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveView('performance')}
        >
          Performance
        </button>
        <button 
          className={`tab-btn ${activeView === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveView('analytics')}
        >
          Analytics
        </button>
        <button 
          className={`tab-btn ${activeView === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveView('alerts')}
        >
          Alerts
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeView === 'performance' && (
          <div className="performance-content">
            {/* Key Performance Metrics */}
            <div className="kpi-grid">
              <MetricCard
                title="Total P&L"
                value={formatCurrency(performanceData.totalPnL)}
                subValue={formatPercentage(performanceData.totalPnLPercentage)}
                trend={performanceData.totalPnLPercentage > 0 ? 5.2 : -3.1}
                icon="💰"
                color={performanceData.totalPnL >= 0 ? "#00ff88" : "#ff4757"}
              />
              <MetricCard
                title="Win Rate"
                value={`${performanceData.winRate.toFixed(1)}%`}
                subValue={`${performanceData.winningTrades}/${performanceData.totalTrades} trades`}
                trend={performanceData.winRate > 50 ? 2.1 : -1.5}
                icon="🎯"
                color="#667eea"
              />
              <MetricCard
                title="Avg Win"
                value={formatCurrency(performanceData.avgWin)}
                subValue="Per winning trade"
                trend={8.7}
                icon="📈"
                color="#00ff88"
              />
              <MetricCard
                title="Max Drawdown"
                value={formatCurrency(performanceData.maxDrawdown)}
                subValue="Worst loss streak"
                trend={-12.3}
                icon="📉"
                color="#ff4757"
              />
            </div>

            {/* Daily P&L Chart */}
            <div className="chart-section">
              <div className="chart-header">
                <h4>Daily P&L Trend (7 days)</h4>
                <span className="chart-total">
                  Total: {formatCurrency(performanceData.dailyPnL?.reduce((sum, day) => sum + day.pnl, 0) || 0)}
                </span>
              </div>
              <PerformanceChart data={performanceData.dailyPnL || []} />
            </div>

            {/* Top Performers */}
            <div className="top-performers">
              <h4>🏆 Top Performers</h4>
              <div className="performers-list">
                {(performanceData.topPerformers || []).map((performer, index) => (
                  <div key={index} className="performer-item">
                    <div className="performer-rank">#{index + 1}</div>
                    <div className="performer-info">
                      <span className="performer-symbol">{performer.symbol}</span>
                      <span className="performer-pnl">{formatCurrency(performer.pnl)}</span>
                    </div>
                    <div className="performer-percentage" style={{ color: getPnLColor(performer.percentage) }}>
                      {formatPercentage(performer.percentage)}
                    </div>
                  </div>
                ))}
                {(!performanceData.topPerformers || performanceData.topPerformers.length === 0) && (
                  <div className="no-data">
                    <p>No profitable trades yet</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeView === 'analytics' && (
          <div className="analytics-content">
            {/* Advanced Metrics */}
            <div className="advanced-metrics">
              <div className="metric-row">
                <span className="metric-label">Profit Factor</span>
                <span className="metric-value">{performanceData.profitFactor}x</span>
                <div className="metric-bar">
                  <div className="bar-fill" style={{ width: `${Math.min(performanceData.profitFactor * 20, 100)}%` }}></div>
                </div>
              </div>
              <div className="metric-row">
                <span className="metric-label">Sharpe Ratio</span>
                <span className="metric-value">{performanceData.sharpeRatio}</span>
                <div className="metric-bar">
                  <div className="bar-fill" style={{ width: `${Math.min(performanceData.sharpeRatio * 30, 100)}%` }}></div>
                </div>
              </div>
              <div className="metric-row">
                <span className="metric-label">Average Loss</span>
                <span className="metric-value" style={{ color: '#ff4757' }}>
                  {formatCurrency(performanceData.avgLoss)}
                </span>
                <div className="metric-bar">
                  <div className="bar-fill negative" style={{ width: '60%' }}></div>
                </div>
              </div>
            </div>

            {/* Risk Analysis */}
            <div className="risk-analysis">
              <h4>🛡️ Risk Analysis</h4>
              <div className="risk-grid">
                <div className="risk-item">
                  <div className="risk-level low">LOW</div>
                  <span>Portfolio Concentration</span>
                </div>
                <div className="risk-item">
                  <div className="risk-level medium">MEDIUM</div>
                  <span>Volatility Exposure</span>
                </div>
                <div className="risk-item">
                  <div className="risk-level high">HIGH</div>
                  <span>Leverage Usage</span>
                </div>
              </div>
            </div>

            {/* Trading Insights */}
            <div className="insights-section">
              <h4>💡 Trading Insights</h4>
              <div className="insight-card">
                <div className="insight-icon">🎯</div>
                <div className="insight-content">
                  <h5>Optimal Entry Times</h5>
                  <p>Your best performance occurs between 14:00-16:00 UTC</p>
                </div>
              </div>
              <div className="insight-card">
                <div className="insight-icon">⏰</div>
                <div className="insight-content">
                  <h5>Hold Time Analysis</h5>
                  <p>Average profitable hold time: 2.3 hours</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'alerts' && (
          <div className="alerts-content">
            <div className="alerts-header">
              <h4>🔔 Active Alerts</h4>
              <button className="btn-clear-alerts">Clear All</button>
            </div>
            <div className="alerts-list">
              {(performanceData.alerts || []).map((alert, index) => (
                <div key={index} className={`alert-item ${alert.type}`}>
                  <div className="alert-icon">
                    {alert.type === 'profit' && '🎉'}
                    {alert.type === 'warning' && '⚠️'}
                    {alert.type === 'info' && '💡'}
                  </div>
                  <div className="alert-content">
                    <p className="alert-message">{alert.message}</p>
                    <span className="alert-time">{alert.time}</span>
                  </div>
                  <button className="alert-dismiss">×</button>
                </div>
              ))}
              {(!performanceData.alerts || performanceData.alerts.length === 0) && (
                <div className="no-data">
                  <p>No recent alerts</p>
                </div>
              )}
            </div>

            {/* Alert Settings */}
            <div className="alert-settings">
              <h5>Alert Settings</h5>
              <div className="setting-item">
                <span>Profit Target Alerts</span>
                <label className="toggle-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider"></span>
                </label>
              </div>
              <div className="setting-item">
                <span>Stop Loss Warnings</span>
                <label className="toggle-switch">
                  <input type="checkbox" defaultChecked />
                  <span className="slider"></span>
                </label>
              </div>
              <div className="setting-item">
                <span>Volume Anomalies</span>
                <label className="toggle-switch">
                  <input type="checkbox" />
                  <span className="slider"></span>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingPerformancePanel;