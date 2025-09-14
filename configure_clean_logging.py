#!/usr/bin/env python3
"""
Configura logging limpo para reduzir spam de erros rotineiros
"""

import logging
import sys

def configure_clean_logging():
    """
    Configura logging inteligente que reduz spam mas mantém informações importantes
    """

    # Configuração principal - nível INFO para mostrar progresso
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('system.log', mode='a')  # Append ao arquivo
        ]
    )

    # Configurar loggers específicos para reduzir spam

    # Logger do Solana Client - menos verboso para consultas de saldo
    solana_logger = logging.getLogger('trade.utils.solana_client')
    solana_logger.setLevel(logging.WARNING)  # Só warnings e errors importantes

    # Logger de HTTP requests - menos verboso
    http_logger = logging.getLogger('httpx')
    http_logger.setLevel(logging.WARNING)

    # Logger de requests - menos verboso
    requests_logger = logging.getLogger('urllib3')
    requests_logger.setLevel(logging.WARNING)

    # Logger de websockets se existir
    ws_logger = logging.getLogger('websockets')
    ws_logger.setLevel(logging.WARNING)

    print("✅ Logging limpo configurado - menos spam, mais informação útil")

if __name__ == "__main__":
    configure_clean_logging()

    # Testar
    logger = logging.getLogger(__name__)
    logger.info("🔥 Teste de logging limpo")
    logger.debug("Debug message - não deve aparecer")
    logger.warning("⚠️ Warning message - deve aparecer")
    logger.error("❌ Error message - deve aparecer")