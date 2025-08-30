import time
from flask import Blueprint, jsonify, request
from backend.services.dextools_service import DEXToolsService
from backend.services.token_analyzer import TokenAnalyzer

api = Blueprint('api', __name__)
dextools = DEXToolsService()
analyzer = TokenAnalyzer()

@api.route('/hot-pools', methods=['GET'])
def get_hot_pools():
    """Get Solana hot pools"""
    try:
        limit = request.args.get('limit', 30, type=int)
        limit = min(max(limit, 1), 100)  # Between 1 and 100
        
        pools = dextools.get_hot_pools(limit)
        print(f"📊 Raw pools received: {len(pools)}")
        
        # Reverse the order so rank 1 appears first (30 to 1 becomes 1 to 30)
        pools.reverse()
        
        # Return raw data with success wrapper
        return jsonify({
            'success': True,
            'data': pools,
            'count': len(pools)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/token/<token_address>', methods=['GET'])
def get_token_analysis(token_address):
    """Get complete token analysis"""
    try:
        analysis = dextools.get_complete_token_analysis(token_address)
        
        # Transform data for frontend
        result = {
            'tokenAddress': token_address,
            'success': analysis['success'],
            'data': {
                'info': {
                    'name': 'N/A',
                    'symbol': 'N/A',
                    'decimals': 0,
                    'logo': '',
                    'description': '',
                    'createdAt': '',
                    'socialInfo': {}
                },
                'price': {
                    'current': 0,
                    'change24h': 0,
                    'change1h': 0,
                    'change6h': 0,
                    'price24hAgo': 0,
                    'price1hAgo': 0
                },
                'score': {
                    'total': 0,
                    'upvotes': 0,
                    'downvotes': 0
                },
                'metrics': {
                    'liquidity_usd': 0,
                    'volume_24h_usd': 0,
                    'volume_1h_usd': 0,
                    'volume_6h_usd': 0,
                    'mcap': 0,
                    'fdv': 0,
                    'circulating_supply': 0,
                    'total_supply': 0,
                    'holders_count': 0,
                    'transactions': 0,
                    'pool_address': '',
                    'dex_info': {}
                },
                'audit': {
                    'is_open_source': 'unknown',
                    'is_honeypot': 'unknown',
                    'is_mintable': 'unknown',
                    'is_proxy': 'unknown',
                    'slippage_modifiable': 'unknown',
                    'is_blacklisted': 'unknown',
                    'is_contract_renounced': 'unknown',
                    'is_potentially_scam': 'unknown',
                    'buy_tax': {'min': 0, 'max': 0, 'status': 'unknown'},
                    'sell_tax': {'min': 0, 'max': 0, 'status': 'unknown'},
                    'updated_at': ''
                },
                'tax_analysis': {
                    'buy_tax_info': {
                        'min_percent': 0,
                        'max_percent': 0,
                        'status': 'unknown',
                        'assessment': ''
                    },
                    'sell_tax_info': {
                        'min_percent': 0,
                        'max_percent': 0,
                        'status': 'unknown',
                        'assessment': ''
                    },
                    'overall_assessment': '',
                    'is_honeypot': 'unknown',
                    'slippage_modifiable': 'unknown',
                    'contract_renounced': 'unknown'
                }
            }
        }
        
        # Process token info
        if analysis['info'] and analysis['info'].get('statusCode') == 200:
            info_data = analysis['info'].get('data', {})
            result['data']['info'] = {
                'name': info_data.get('name', 'N/A'),
                'symbol': info_data.get('symbol', 'N/A'),
                'decimals': info_data.get('decimals', 0),
                'logo': info_data.get('logo', ''),
                'description': info_data.get('description', ''),
                'createdAt': info_data.get('creationTime', ''),
                'socialInfo': info_data.get('socialInfo', {})
            }
        
        # Process price info
        if analysis['price'] and analysis['price'].get('statusCode') == 200:
            price_data = analysis['price'].get('data', {})
            result['data']['price'] = {
                'current': price_data.get('price', 0),
                'change24h': price_data.get('variation24h', 0),
                'change1h': price_data.get('variation1h', 0),
                'change6h': price_data.get('variation6h', 0),
                'price24hAgo': price_data.get('price24h', 0),
                'price1hAgo': price_data.get('price1h', 0)
            }
        
        # Process score info
        if analysis['score'] and analysis['score'].get('statusCode') == 200:
            score_data = analysis['score'].get('data', {})
            dext_score = score_data.get('dextScore', {})
            votes = score_data.get('votes', {})
            
            result['data']['score'] = {
                'total': dext_score.get('total', 0),
                'upvotes': votes.get('upvotes', 0),
                'downvotes': votes.get('downvotes', 0)
            }
        
        # Process comprehensive metrics info
        if analysis['metrics'] and analysis['metrics'].get('statusCode') == 200:
            metrics_data = analysis['metrics'].get('data', {})
            
            result['data']['metrics'] = {
                'liquidity_usd': metrics_data.get('liquidity_usd', 0),
                'volume_24h_usd': metrics_data.get('volume_24h_usd', 0),
                'volume_1h_usd': metrics_data.get('volume_1h_usd', 0),
                'volume_6h_usd': metrics_data.get('volume_6h_usd', 0),
                'mcap': metrics_data.get('mcap', 0),
                'fdv': metrics_data.get('fdv', 0),
                'circulating_supply': metrics_data.get('circulating_supply', 0),
                'total_supply': metrics_data.get('total_supply', 0),
                'holders_count': metrics_data.get('holders_count', 0),
                'transactions': metrics_data.get('transactions', 0),
                'pool_address': metrics_data.get('pool_address', ''),
                'dex_info': metrics_data.get('dex_info', {})
            }
        
        # Process audit info
        if analysis['audit'] and analysis['audit'].get('statusCode') == 200:
            audit_data = analysis['audit'].get('data', {})
            
            result['data']['audit'] = {
                'is_open_source': audit_data.get('is_open_source', 'unknown'),
                'is_honeypot': audit_data.get('is_honeypot', 'unknown'),
                'is_mintable': audit_data.get('is_mintable', 'unknown'),
                'is_proxy': audit_data.get('is_proxy', 'unknown'),
                'slippage_modifiable': audit_data.get('slippage_modifiable', 'unknown'),
                'is_blacklisted': audit_data.get('is_blacklisted', 'unknown'),
                'is_contract_renounced': audit_data.get('is_contract_renounced', 'unknown'),
                'is_potentially_scam': audit_data.get('is_potentially_scam', 'unknown'),
                'buy_tax': {
                    'min': audit_data.get('buy_tax', {}).get('min') or 0,
                    'max': audit_data.get('buy_tax', {}).get('max') or 0,
                    'status': audit_data.get('buy_tax', {}).get('status', 'unknown')
                },
                'sell_tax': {
                    'min': audit_data.get('sell_tax', {}).get('min') or 0,
                    'max': audit_data.get('sell_tax', {}).get('max') or 0,
                    'status': audit_data.get('sell_tax', {}).get('status', 'unknown')
                },
                'updated_at': audit_data.get('updated_at', '')
            }
        
        # Process tax analysis info
        if analysis['tax_analysis'] and analysis['tax_analysis'].get('statusCode') == 200:
            tax_data = analysis['tax_analysis'].get('data', {})
            
            buy_tax_info = tax_data.get('buy_tax_info', {})
            sell_tax_info = tax_data.get('sell_tax_info', {})
            
            result['data']['tax_analysis'] = {
                'buy_tax_info': {
                    'min_percent': buy_tax_info.get('min_percent') or 0,
                    'max_percent': buy_tax_info.get('max_percent') or 0,
                    'status': buy_tax_info.get('status', 'unknown'),
                    'assessment': buy_tax_info.get('assessment', '')
                },
                'sell_tax_info': {
                    'min_percent': sell_tax_info.get('min_percent') or 0,
                    'max_percent': sell_tax_info.get('max_percent') or 0,
                    'status': sell_tax_info.get('status', 'unknown'),
                    'assessment': sell_tax_info.get('assessment', '')
                },
                'overall_assessment': tax_data.get('overall_assessment', ''),
                'is_honeypot': tax_data.get('is_honeypot', 'unknown'),
                'slippage_modifiable': tax_data.get('slippage_modifiable', 'unknown'),
                'contract_renounced': tax_data.get('contract_renounced', 'unknown')
            }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'tokenAddress': token_address
        }), 500

@api.route('/analyzer/start', methods=['POST'])
def start_analyzer():
    """Start the background token analyzer"""
    try:
        analyzer.start_background_analysis()
        return jsonify({
            'success': True,
            'message': 'Token analyzer started',
            'status': analyzer.get_analysis_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/analyzer/stop', methods=['POST'])
def stop_analyzer():
    """Stop the background token analyzer"""
    try:
        analyzer.stop_background_analysis()
        return jsonify({
            'success': True,
            'message': 'Token analyzer stopped'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/analyzer/status', methods=['GET'])
def get_analyzer_status():
    """Get analyzer status"""
    return jsonify({
        'success': True,
        'data': analyzer.get_analysis_status()
    })

@api.route('/analyzer/suggestions', methods=['GET'])
def get_suggestions():
    """Get approved token suggestions"""
    return jsonify({
        'success': True,
        'data': {
            'approved': analyzer.get_approved_tokens(),
            'rejected': analyzer.get_rejected_tokens()
        }
    })

@api.route('/analyzer/criteria', methods=['GET'])
def get_criteria():
    """Get analysis criteria"""
    return jsonify({
        'success': True,
        'data': analyzer.criteria
    })

@api.route('/analyzer/criteria', methods=['PUT'])
def update_criteria():
    """Update analysis criteria"""
    try:
        new_criteria = request.get_json()
        analyzer.update_criteria(new_criteria)
        return jsonify({
            'success': True,
            'message': 'Criteria updated',
            'data': analyzer.criteria
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Solana Hot Pools API',
        'analyzer_running': analyzer.is_running,
        'timestamp': time.time()
    })