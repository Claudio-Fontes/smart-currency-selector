import { useState, useEffect } from 'react';

const usePositions = (refreshInterval = 60000) => { // 60 segundos
    const [positions, setPositions] = useState([]);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchPositions = async () => {
        console.log('🏛️ usePositions: Fetching positions...');
        try {
            setError(null);
            console.log('🏛️ usePositions: Making fetch request to /api/positions');
            const response = await fetch('/api/positions');
            console.log('🏛️ usePositions: Response status:', response.status, response.statusText);
            const data = await response.json();
            console.log('🏛️ usePositions: Received data:', data);

            if (data.success) {
                console.log('🏛️ usePositions: Data success, setting positions:', data.data.positions.length);
                setPositions(data.data.positions);
                setSummary(data.data.summary);
                setLastUpdate(new Date());
                console.log('🏛️ usePositions: State updated successfully');
            } else {
                console.error('🏛️ usePositions: Data not successful:', data.error);
                throw new Error(data.error || 'Failed to fetch positions');
            }
        } catch (err) {
            console.error('Error fetching positions:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Buscar posições imediatamente
        fetchPositions();

        // Configurar intervalo de atualização
        const interval = setInterval(fetchPositions, refreshInterval);

        // Cleanup
        return () => clearInterval(interval);
    }, [refreshInterval]);

    return {
        positions,
        summary,
        loading,
        error,
        lastUpdate,
        refetch: fetchPositions
    };
};

export default usePositions;