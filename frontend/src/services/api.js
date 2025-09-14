import axios from 'axios';

// Use relative URLs to go through webpack proxy
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 second timeout for market intelligence
  headers: {
    'Content-Type': 'application/json',
  },
});

export const hotPoolsAPI = {
  getHotPools: async (limit = 50) => {
    try {
      const response = await api.get(`/hot-pools?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching hot pools:', error);
      throw error;
    }
  },

  getTokenAnalysis: async (tokenAddress, retries = 3) => {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        console.log(`Fetching token analysis for ${tokenAddress} (attempt ${attempt}/${retries})`);
        const response = await api.get(`/token/${tokenAddress}`);
        
        if (response.data && response.data.success) {
          console.log(`✅ Token analysis successful for ${tokenAddress}`);
          return response.data;
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error(`❌ Attempt ${attempt} failed for token ${tokenAddress}:`, error.message);
        
        if (attempt === retries) {
          // Last attempt failed
          const errorMessage = error.response?.status === 404 
            ? 'Token not found' 
            : error.code === 'ECONNABORTED' 
            ? 'Request timeout' 
            : 'Network error';
          
          throw new Error(errorMessage);
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  },

  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
};

export const analyzerAPI = {
  start: async () => {
    try {
      const response = await api.post('/analyzer/start');
      return response.data;
    } catch (error) {
      console.error('Error starting analyzer:', error);
      throw error;
    }
  },

  stop: async () => {
    try {
      const response = await api.post('/analyzer/stop');
      return response.data;
    } catch (error) {
      console.error('Error stopping analyzer:', error);
      throw error;
    }
  },

  getStatus: async () => {
    try {
      const response = await api.get('/analyzer/status');
      return response.data;
    } catch (error) {
      console.error('Error getting analyzer status:', error);
      throw error;
    }
  },

  getSuggestions: async () => {
    try {
      const response = await api.get('/analyzer/suggestions');
      return response.data;
    } catch (error) {
      console.error('Error getting suggestions:', error);
      throw error;
    }
  },

  getCriteria: async () => {
    try {
      const response = await api.get('/analyzer/criteria');
      return response.data;
    } catch (error) {
      console.error('Error getting criteria:', error);
      throw error;
    }
  },

  updateCriteria: async (criteria) => {
    try {
      const response = await api.put('/analyzer/criteria', criteria);
      return response.data;
    } catch (error) {
      console.error('Error updating criteria:', error);
      throw error;
    }
  }
};

export const marketIntelligenceAPI = {
  getMarketIntelligence: async (tokenAddress) => {
    try {
      console.log(`🔄 Fetching market intelligence for: ${tokenAddress}`);
      const response = await api.get(`/market-intelligence/${tokenAddress}`);
      
      if (response.data && response.data.success) {
        console.log('✅ Market intelligence fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching market intelligence:', error);
      throw error;
    }
  },

  // Fast loading - get basic data quickly
  getMarketIntelligenceFast: async (tokenAddress) => {
    try {
      console.log(`🚀 Fetching FAST market intelligence for: ${tokenAddress}`);
      const response = await api.get(`/market-intelligence-fast/${tokenAddress}`, {
        timeout: 15000 // Short timeout for fast endpoint
      });
      
      if (response.data && response.data.success) {
        console.log('⚡ Fast market intelligence fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching fast market intelligence:', error);
      throw error;
    }
  },

  // Enhanced data - for background loading
  getMarketIntelligenceEnhanced: async (tokenAddress) => {
    try {
      console.log(`🔍 Fetching ENHANCED market intelligence for: ${tokenAddress}`);
      const response = await api.get(`/market-intelligence/enhanced/${tokenAddress}`, {
        timeout: 30000
      });
      
      if (response.data && response.data.success) {
        console.log('🎯 Enhanced market intelligence fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching enhanced market intelligence:', error);
      throw error;
    }
  },

  // Metrics data - for background loading
  getMarketIntelligenceMetrics: async (tokenAddress) => {
    try {
      console.log(`📊 Fetching METRICS for: ${tokenAddress}`);
      const response = await api.get(`/market-intelligence/metrics/${tokenAddress}`, {
        timeout: 25000
      });
      
      if (response.data && response.data.success) {
        console.log('📈 Metrics fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching metrics:', error);
      throw error;
    }
  }
};

export const tradingAPI = {
  getStatistics: async () => {
    try {
      console.log('🔄 Fetching trading statistics...');
      const response = await api.get('/trades/statistics');
      
      if (response.data && response.data.success) {
        console.log('✅ Trading statistics fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching trading statistics:', error);
      throw error;
    }
  },

  getPositions: async () => {
    try {
      console.log('🔄 Fetching trading positions...');
      const response = await api.get('/positions');
      
      if (response.data && response.data.success) {
        console.log('✅ Trading positions fetched successfully');
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('❌ Error fetching trading positions:', error);
      throw error;
    }
  }
};

export default api;