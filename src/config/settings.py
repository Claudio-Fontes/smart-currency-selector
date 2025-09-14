import os
from typing import Dict, Any


def load_settings() -> Dict[str, Any]:
    """Carrega todas as configurações das variáveis de ambiente"""
    return {
        'dextools': {
            'api_key': os.getenv('DEXTOOLS_API_KEY'),
            'base_url': os.getenv('DEXTOOLS_BASE_URL', 'https://public-api.dextools.io/v2')
        },
        'postgres': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'database': os.getenv('POSTGRES_DB')
        },
        'chains': {
            "1": "eth",
            "2": "bsc", 
            "3": "polygon",
            "4": "arbitrum",
            "5": "avalanche"
        }
    }


def validate_settings(settings: Dict[str, Any]) -> bool:
    """Valida se as configurações obrigatórias estão presentes"""
    if not settings['dextools']['api_key']:
        print("❌ ERRO: DEXTOOLS_API_KEY não encontrada no arquivo .env")
        print("   1. Copie .env.example para .env")
        print("   2. Adicione sua API key da DEXTools")
        return False
    return True