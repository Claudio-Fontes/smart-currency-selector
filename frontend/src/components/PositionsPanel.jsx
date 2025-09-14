import React from 'react';
import usePositions from '../hooks/usePositions';
import PositionCard from './PositionCard';
import PositionsSummary from './PositionsSummary';

const PositionsPanel = () => {
    console.log('🏛️ PositionsPanel: Component mounted');
    const { positions, summary, loading, error, lastUpdate, refetch } = usePositions(60000); // Atualiza a cada 60 segundos
    
    console.log('🏛️ PositionsPanel:', { positions: positions?.length, summary, loading, error });

    if (loading) {
        return (
            <div className="positions-panel loading">
                <div className="panel-header">
                    <h2>📊 MONITOR DE POSIÇÕES</h2>
                    <div className="loading-indicator">Carregando...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="positions-panel error">
                <div className="panel-header">
                    <h2>📊 MONITOR DE POSIÇÕES</h2>
                    <button onClick={refetch} className="refresh-btn">🔄 Tentar Novamente</button>
                </div>
                <div className="error-message">
                    ❌ Erro: {error}
                </div>
            </div>
        );
    }

    // Dividir posições em 3 colunas de forma equilibrada
    const positionsPerColumn = Math.ceil(positions.length / 3);
    const column1 = positions.slice(0, positionsPerColumn);
    const column2 = positions.slice(positionsPerColumn, positionsPerColumn * 2);
    const column3 = positions.slice(positionsPerColumn * 2);

    return (
        <div className="positions-panel">
            <div className="panel-header">
                <h2>📊 MONITOR DE POSIÇÕES</h2>
                <div className="header-controls">
                    {lastUpdate && (
                        <span className="last-update">
                            🕐 {lastUpdate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                    )}
                    <button onClick={refetch} className="refresh-btn" title="Atualizar agora">
                        🔄
                    </button>
                </div>
            </div>

            {/* Resumo das estatísticas no topo */}
            <PositionsSummary summary={summary} lastUpdate={lastUpdate} />

            {positions.length === 0 ? (
                <div className="no-positions">
                    <div className="no-positions-message">
                        📭 Nenhuma posição aberta no momento
                    </div>
                </div>
            ) : (
                <>
                    <div className="positions-count-header">
                        📈 {positions.length} POSIÇÕES ABERTAS:
                    </div>

                    <div className="positions-grid">
                        <div className="positions-column">
                            {column1.map((position, index) => (
                                <PositionCard key={position.id} position={position} />
                            ))}
                        </div>

                        <div className="positions-column">
                            {column2.map((position, index) => (
                                <PositionCard key={position.id} position={position} />
                            ))}
                        </div>

                        <div className="positions-column">
                            {column3.map((position, index) => (
                                <PositionCard key={position.id} position={position} />
                            ))}
                        </div>
                    </div>
                </>
            )}

            <div className="panel-footer">
                <div className="auto-refresh-info">
                    ⏱️ Atualização automática a cada 60 segundos
                </div>
            </div>
        </div>
    );
};

export default PositionsPanel;