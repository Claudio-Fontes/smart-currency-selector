import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import os

logger = logging.getLogger(__name__)

class SocialEnhancedService:
    """
    Serviço que busca tokens dos hot pools e enriquece com informações sociais
    """
    def __init__(self):
        self.api_key = os.getenv('DEXTOOLS_API_KEY')
        self.base_url = 'https://api.dextools.io/v2'
        self.headers = {}
        if self.api_key:
            self.headers['X-API-KEY'] = self.api_key
        self.headers['Accept'] = 'application/json'
    
    async def get_hot_pools_with_social(self, chain: str = 'solana') -> List[Dict]:
        """
        Busca hot pools e enriquece com informações sociais dos tokens
        """
        try:
            # Buscar hot pools
            url = f"{self.base_url}/ranking/{chain}/hotpools"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Processar cada pool
                        enhanced_pools = []
                        for pool in data[:20]:  # Top 20 apenas
                            enhanced = await self._enhance_with_social(pool, chain, session)
                            enhanced_pools.append(enhanced)
                        
                        return enhanced_pools
                    else:
                        logger.error(f"Error fetching hot pools: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to fetch hot pools with social: {e}")
            return []
    
    async def _enhance_with_social(self, pool: Dict, chain: str, session) -> Dict:
        """
        Enriquece pool com informações sociais do token
        """
        try:
            main_token = pool.get('mainToken', {})
            token_address = main_token.get('address')
            
            if not token_address:
                return pool
            
            # Buscar informações do token
            url = f"{self.base_url}/token/{chain}/{token_address}"
            
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Adicionar informações sociais ao pool
                    social_info = token_data.get('socialInfo', {})
                    
                    # Calcular métricas sociais
                    social_count = sum(1 for v in social_info.values() if v and v != 'N/A')
                    
                    social_score = 0
                    if social_info.get('website'):
                        social_score += 30
                    if social_info.get('twitter'):
                        social_score += 25
                    if social_info.get('telegram'):
                        social_score += 25
                    if social_info.get('discord'):
                        social_score += 10
                    if social_info.get('github'):
                        social_score += 10
                    
                    pool['socialMetrics'] = {
                        'score': social_score,
                        'count': social_count,
                        'hasTwitter': bool(social_info.get('twitter')),
                        'hasTelegram': bool(social_info.get('telegram')),
                        'hasWebsite': bool(social_info.get('website'))
                    }
                    
                    pool['socialInfo'] = social_info
                    
                    # Classificar momentum social
                    if social_score >= 80:
                        pool['socialMomentum'] = 'STRONG 🔥'
                    elif social_score >= 60:
                        pool['socialMomentum'] = 'MODERATE 📈'
                    elif social_score >= 40:
                        pool['socialMomentum'] = 'GROWING 🌱'
                    else:
                        pool['socialMomentum'] = 'LOW 💤'
                    
                    return pool
                else:
                    # Se não conseguir buscar info social, retorna pool original
                    pool['socialMetrics'] = {
                        'score': 0,
                        'count': 0,
                        'hasTwitter': False,
                        'hasTelegram': False,
                        'hasWebsite': False
                    }
                    pool['socialMomentum'] = 'UNKNOWN ❓'
                    return pool
                    
        except Exception as e:
            logger.error(f"Error enhancing pool with social: {e}")
            pool['socialMetrics'] = {
                'score': 0,
                'count': 0,
                'hasTwitter': False,
                'hasTelegram': False,
                'hasWebsite': False
            }
            pool['socialMomentum'] = 'ERROR ⚠️'
            return pool
    
    async def get_social_rankings(self, chain: str = 'solana') -> Dict:
        """
        Retorna rankings baseados em métricas sociais dos hot pools
        """
        try:
            pools = await self.get_hot_pools_with_social(chain)
            
            if not pools:
                return {
                    'most_social': [],
                    'strong_momentum': [],
                    'emerging': []
                }
            
            # Filtrar pools com métricas sociais
            pools_with_social = [p for p in pools if p.get('socialMetrics', {}).get('score', 0) > 0]
            
            # Ordenar por score social
            most_social = sorted(
                pools_with_social,
                key=lambda x: x.get('socialMetrics', {}).get('score', 0),
                reverse=True
            )[:10]
            
            # Filtrar por momentum forte
            strong_momentum = [
                p for p in pools_with_social 
                if 'STRONG' in p.get('socialMomentum', '')
            ][:10]
            
            # Filtrar emergentes (score entre 40-70)
            emerging = [
                p for p in pools_with_social
                if 40 <= p.get('socialMetrics', {}).get('score', 0) < 70
            ][:10]
            
            return {
                'most_social': most_social,
                'strong_momentum': strong_momentum,
                'emerging': emerging
            }
            
        except Exception as e:
            logger.error(f"Failed to get social rankings: {e}")
            return {
                'most_social': [],
                'strong_momentum': [],
                'emerging': []
            }

# Instância global
social_enhanced_service = SocialEnhancedService()