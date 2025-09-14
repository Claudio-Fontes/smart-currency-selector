from flask import Blueprint, jsonify, request
from backend.services.social_tokens_service import social_tokens_service
import asyncio
import logging

logger = logging.getLogger(__name__)

social_bp = Blueprint('social', __name__)

@social_bp.route('/api/social/trending', methods=['GET'])
def get_social_trending():
    """
    Endpoint para buscar tokens trending por atividade social
    
    Query params:
    - chain: blockchain (default: ether)
    - limit: número de tokens (default: 50)
    """
    try:
        chain = request.args.get('chain', 'ether')
        limit = int(request.args.get('limit', 50))
        
        # Executar função assíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tokens = loop.run_until_complete(
            social_tokens_service.get_social_trending_tokens(chain, limit)
        )
        
        # Adicionar análise de momentum
        tokens_with_momentum = loop.run_until_complete(
            social_tokens_service.analyze_social_momentum(tokens)
        )
        
        return jsonify({
            'success': True,
            'chain': chain,
            'count': len(tokens_with_momentum),
            'tokens': tokens_with_momentum
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_social_trending: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_bp.route('/api/social/rankings', methods=['GET'])
def get_social_rankings():
    """
    Endpoint para obter rankings baseados em métricas sociais
    
    Query params:
    - chain: blockchain (default: ether)
    """
    try:
        chain = request.args.get('chain', 'ether')
        
        # Executar função assíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rankings = loop.run_until_complete(
            social_tokens_service.get_social_rankings(chain)
        )
        
        return jsonify({
            'success': True,
            'chain': chain,
            'rankings': {
                'most_social': rankings['most_social'][:10],
                'recently_updated': rankings['recently_updated'][:10],
                'high_engagement': rankings['high_engagement'][:10]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_social_rankings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_bp.route('/api/social/token/<chain>/<address>', methods=['GET'])
def get_token_social_details(chain, address):
    """
    Endpoint para obter detalhes sociais de um token específico
    
    Path params:
    - chain: blockchain
    - address: endereço do token
    """
    try:
        # Executar função assíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        token_details = loop.run_until_complete(
            social_tokens_service.get_token_social_details(chain, address)
        )
        
        if token_details:
            return jsonify({
                'success': True,
                'token': token_details
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Token not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in get_token_social_details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_bp.route('/api/social/stats', methods=['GET'])
def get_social_stats():
    """
    Endpoint para obter estatísticas gerais de tokens sociais
    """
    try:
        chains = ['ether', 'bsc', 'polygon']
        stats = {}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for chain in chains:
            tokens = loop.run_until_complete(
                social_tokens_service.get_social_trending_tokens(chain, limit=20)
            )
            
            if tokens:
                avg_social_score = sum(t['social_metrics']['social_score'] for t in tokens) / len(tokens)
                total_with_twitter = sum(1 for t in tokens if t['social_metrics']['has_twitter'])
                total_with_telegram = sum(1 for t in tokens if t['social_metrics']['has_telegram'])
                
                stats[chain] = {
                    'total_tokens': len(tokens),
                    'avg_social_score': round(avg_social_score, 1),
                    'with_twitter': total_with_twitter,
                    'with_telegram': total_with_telegram
                }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_social_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500