import { useState, useEffect, useCallback } from 'react';
import { analyzerAPI } from '../services/api';

export const useAnalyzer = () => {
  const [status, setStatus] = useState(null);
  const [suggestions, setSuggestions] = useState({ approved: [], rejected: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusResponse, suggestionsResponse] = await Promise.all([
        analyzerAPI.getStatus(),
        analyzerAPI.getSuggestions()
      ]);

      if (statusResponse.success) {
        setStatus(statusResponse.data);
      }

      if (suggestionsResponse.success) {
        setSuggestions(suggestionsResponse.data);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch analyzer data');
      console.error('Error fetching analyzer data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const startAnalyzer = useCallback(async () => {
    try {
      await analyzerAPI.start();
      await fetchData();
    } catch (err) {
      setError('Failed to start analyzer');
      console.error('Error starting analyzer:', err);
    }
  }, [fetchData]);

  const stopAnalyzer = useCallback(async () => {
    try {
      await analyzerAPI.stop();
      await fetchData();
    } catch (err) {
      setError('Failed to stop analyzer');
      console.error('Error stopping analyzer:', err);
    }
  }, [fetchData]);

  const getTokenStatus = useCallback((tokenAddress) => {
    if (!tokenAddress) return null;

    // Check approved tokens
    const approved = suggestions.approved.find(token => 
      token.token_address === tokenAddress
    );
    if (approved) {
      return {
        status: 'approved',
        score: approved.evaluation?.score || 0,
        warnings: approved.evaluation?.warnings || [],
        data: approved
      };
    }

    // Check rejected tokens
    const rejected = suggestions.rejected.find(token => 
      token.token_address === tokenAddress
    );
    if (rejected) {
      return {
        status: 'rejected',
        reasons: rejected.rejection_reasons || [],
        data: rejected
      };
    }

    return null;
  }, [suggestions]);

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);

    return () => clearInterval(interval);
  }, [fetchData]);

  return {
    status,
    suggestions,
    loading,
    error,
    fetchData,
    startAnalyzer,
    stopAnalyzer,
    getTokenStatus
  };
};