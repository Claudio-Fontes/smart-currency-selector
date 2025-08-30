import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increased timeout for heavy operations
  headers: {
    'Content-Type': 'application/json',
  },
});

export const hotPoolsAPI = {
  getHotPools: async (limit = 30) => {
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

export default api;