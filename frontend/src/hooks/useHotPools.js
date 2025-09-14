import { useState, useEffect, useCallback, useRef } from 'react';
import { hotPoolsAPI } from '../services/api';

// Simple, stable hook for hot pools
export const useHotPools = (limit = 50) => {
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const mounted = useRef(true);

  const fetchPools = useCallback(async () => {
    if (!mounted.current) return;
    
    try {
      console.log('🔄 Fetching hot pools with limit:', limit);
      setLoading(true);
      setError(null);
      
      const response = await hotPoolsAPI.getHotPools(limit);
      console.log('📡 Hot pools response:', response);
      
      if (!mounted.current) return;
      
      if (response && response.success) {
        console.log('✅ Setting pools:', response.data?.length || 0, 'pools');
        setPools(response.data || []);
      } else {
        console.log('❌ Response not successful:', response);
        setError('Failed to fetch pools');
        setPools([]);
      }
    } catch (err) {
      if (mounted.current) {
        console.error('❌ Error fetching hot pools:', err);
        setError('Network error');
        setPools([]);
      }
    } finally {
      if (mounted.current) {
        setLoading(false);
      }
    }
  }, [limit]);

  useEffect(() => {
    mounted.current = true;
    fetchPools();
    
    return () => {
      mounted.current = false;
    };
  }, [fetchPools]);

  const refetch = useCallback(() => {
    if (mounted.current) {
      fetchPools();
    }
  }, [fetchPools]);

  return { pools, loading, error, refetch };
};

// Simplified token analysis hook
export const useTokenAnalysis = () => {
  const [data, setData] = useState({
    analysis: null,
    loading: false,
    error: null
  });
  const mounted = useRef(true);
  const currentToken = useRef(null);

  const fetchToken = useCallback(async (tokenAddress) => {
    if (!tokenAddress || !mounted.current) return;
    
    // Skip if we're already fetching this token
    if (currentToken.current === tokenAddress) return;
    
    currentToken.current = tokenAddress;
    
    if (!mounted.current) return;
    
    setData({ analysis: null, loading: true, error: null });
    
    try {
      const response = await hotPoolsAPI.getTokenAnalysis(tokenAddress);
      
      if (!mounted.current || currentToken.current !== tokenAddress) return;
      
      if (response && response.success) {
        console.log(`✅ Successfully loaded analysis for ${tokenAddress}`);
        setData({ analysis: response, loading: false, error: null });
      } else {
        console.warn(`❌ API returned unsuccessful response for ${tokenAddress}`);
        setData({ analysis: null, loading: false, error: 'Token analysis not available' });
      }
    } catch (err) {
      if (mounted.current && currentToken.current === tokenAddress) {
        console.error(`❌ Error analyzing token ${tokenAddress}:`, err.message);
        const errorMessage = err.message || 'Network error';
        setData({ analysis: null, loading: false, error: errorMessage });
      }
    }
  }, []);

  const clear = useCallback(() => {
    if (mounted.current) {
      currentToken.current = null;
      setData({ analysis: null, loading: false, error: null });
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      currentToken.current = null;
    };
  }, []);

  return {
    analysis: data.analysis,
    loading: data.loading,
    error: data.error,
    fetchTokenAnalysis: fetchToken,
    clearAnalysis: clear
  };
};