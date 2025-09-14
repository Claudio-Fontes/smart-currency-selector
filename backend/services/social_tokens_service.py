import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import os

logger = logging.getLogger(__name__)

class SocialTokensService:
    def __init__(self):
        self.api_key = os.getenv('DEXTOOLS_API_KEY')
        self.base_url = os.getenv('DEXTOOLS_BASE_URL', 'https://public-api.dextools.io/standard/v2')
        
        # Garantir que não há None nos headers
        self.headers = {}
        if self.api_key:
            self.headers['X-API-KEY'] = self.api_key
        self.headers['Accept'] = 'application/json'
    
    async def get_social_trending_tokens(self, chain: str = 'ether', limit: int = 50) -> List[Dict]:
        """
        Busca tokens ordenados por atualização de informações sociais
        
        Args:
            chain: Blockchain (ether, bsc, polygon, etc)
            limit: Número de tokens a retornar
        
        Returns:
            Lista de tokens com informações sociais
        """
        try:
            # Data range - últimos 7 dias
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=7)
            
            params = {
                'sort': 'socialsInfoUpdated',
                'order': 'desc',
                'from': from_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'to': to_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'page': '0',
                'pageSize': str(limit)
            }
            
            url = f"{self.base_url}/token/{chain}"
            
            print(f"🔍 Fetching social tokens from: {url}")
            print(f"📋 Params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    response_text = await response.text()
                    print(f"📊 Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        tokens = data.get('results', [])
                        print(f"✅ Found {len(tokens)} tokens")
                        
                        # Processar e enriquecer dados
                        processed_tokens = []
                        for token in tokens:
                            processed = await self._process_social_token(token, chain)
                            if processed:
                                processed_tokens.append(processed)
                        
                        return processed_tokens
                    else:
                        print(f"❌ Error response: {response_text[:500]}")
                        logger.error(f"Error fetching social tokens: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Exception: {e}")
            logger.error(f"Failed to fetch social trending tokens: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _process_social_token(self, token: Dict, chain: str) -> Optional[Dict]:
        """
        Processa e enriquece informações do token social
        """
        try:
            social_info = token.get('socialInfo', {})
            
            # Contar quantas redes sociais estão ativas
            social_count = sum(1 for v in social_info.values() if v and v != 'N/A')
            
            # Verificar presença em redes principais
            has_twitter = bool(social_info.get('twitter'))
            has_telegram = bool(social_info.get('telegram'))
            has_website = bool(social_info.get('website'))
            
            # Calcular score social básico
            social_score = 0
            if has_website:
                social_score += 30
            if has_twitter:
                social_score += 25
            if has_telegram:
                social_score += 25
            if social_info.get('discord'):
                social_score += 10
            if social_info.get('github'):
                social_score += 10
            
            return {
                'chain': chain,
                'address': token.get('address'),
                'name': token.get('name'),
                'symbol': token.get('symbol'),
                'logo': token.get('logo'),
                'description': token.get('description', ''),
                'decimals': token.get('decimals'),
                'creation_time': token.get('creationTime'),
                'social_info': social_info,
                'social_metrics': {
                    'social_count': social_count,
                    'social_score': social_score,
                    'has_twitter': has_twitter,
                    'has_telegram': has_telegram,
                    'has_website': has_website,
                    'last_social_update': token.get('socialsInfoUpdated')
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing social token: {e}")
            return None
    
    async def get_token_social_details(self, chain: str, address: str) -> Optional[Dict]:
        """
        Busca detalhes sociais específicos de um token
        """
        try:
            url = f"{self.base_url}/token/{chain}/{address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_social_token(data, chain)
                    else:
                        logger.error(f"Error fetching token details: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to fetch token social details: {e}")
            return None
    
    async def analyze_social_momentum(self, tokens: List[Dict]) -> List[Dict]:
        """
        Analisa momentum social dos tokens
        """
        analyzed = []
        
        for token in tokens:
            metrics = token.get('social_metrics', {})
            
            # Classificar momentum
            if metrics.get('social_score', 0) >= 80:
                momentum = 'STRONG'
                momentum_emoji = '🔥'
            elif metrics.get('social_score', 0) >= 60:
                momentum = 'MODERATE'
                momentum_emoji = '📈'
            elif metrics.get('social_score', 0) >= 40:
                momentum = 'GROWING'
                momentum_emoji = '🌱'
            else:
                momentum = 'LOW'
                momentum_emoji = '💤'
            
            token['social_momentum'] = {
                'level': momentum,
                'emoji': momentum_emoji,
                'score': metrics.get('social_score', 0)
            }
            
            analyzed.append(token)
        
        return analyzed
    
    async def get_social_rankings(self, chain: str = 'ether') -> Dict:
        """
        Retorna rankings baseados em métricas sociais
        """
        try:
            tokens = await self.get_social_trending_tokens(chain, limit=100)
            
            if not tokens:
                return {
                    'most_social': [],
                    'recently_updated': [],
                    'high_engagement': []
                }
            
            # Ordenar por diferentes critérios
            most_social = sorted(
                tokens, 
                key=lambda x: x['social_metrics']['social_count'], 
                reverse=True
            )[:20]
            
            recently_updated = sorted(
                tokens,
                key=lambda x: x['social_metrics'].get('last_social_update', ''),
                reverse=True
            )[:20]
            
            high_engagement = sorted(
                tokens,
                key=lambda x: x['social_metrics']['social_score'],
                reverse=True
            )[:20]
            
            return {
                'most_social': most_social,
                'recently_updated': recently_updated,
                'high_engagement': high_engagement
            }
            
        except Exception as e:
            logger.error(f"Failed to get social rankings: {e}")
            return {
                'most_social': [],
                'recently_updated': [],
                'high_engagement': []
            }

# Instância global
social_tokens_service = SocialTokensService()