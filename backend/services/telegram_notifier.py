import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import requests
from decimal import Decimal
import os

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("⚠️ Telegram notifications disabled - missing BOT_TOKEN or CHAT_ID")
        else:
            logger.info("✅ Telegram notifications enabled")
    
    def send_token_suggestion(self, token_data: Dict, evaluation: Dict) -> bool:
        """Send token suggestion notification to Telegram"""
        if not self.enabled:
            return False
        
        try:
            message = self._format_token_message(token_data, evaluation)
            return self._send_message(message)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def _format_token_message(self, token_data: Dict, evaluation: Dict) -> str:
        """Format token data into a readable Telegram message"""
        
        # Extract basic info
        symbol = token_data.get('symbol', 'Unknown')
        name = token_data.get('name', 'Unknown')
        token_address = token_data.get('token_address', 'N/A')
        price = token_data.get('price', 0)
        
        # Extract analysis data
        score = evaluation.get('score', 0)
        liquidity = token_data.get('liquidity', 0)
        volume_24h = token_data.get('volume_24h', 0)
        market_cap = token_data.get('market_cap', 0)
        holders = token_data.get('holders_count', 0)
        dext_score = token_data.get('dext_score', 0)
        
        # Calculate volume/liquidity ratio
        vol_liq_ratio = (volume_24h / liquidity) if liquidity > 0 else 0
        
        # Format price
        price_str = self._format_price(price)
        
        # Create message
        message = f"""🚀 <b>NOVA MOEDA SUGERIDA!</b>

💰 <b>{symbol}</b> - {name}
💵 Preço: <b>${price_str}</b>
📊 Score IA: <b>{score:.1f}/100</b>

📈 <b>MÉTRICAS:</b>
💧 Liquidez: ${liquidity:,.0f}
📊 Volume 24h: ${volume_24h:,.0f}
📉 Market Cap: ${market_cap:,.0f}
👥 Holders: {holders:,}
🔒 DEXT Score: {dext_score}/100

⚡ <b>ANÁLISE:</b>
🎯 Ratio V/L: {vol_liq_ratio:.2f}x
{self._get_ratio_status(vol_liq_ratio)}

📝 <b>Token:</b> <code>{token_address}</code>

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

<i>Sistema Smart Currency Selector v2.0</i>"""

        return message
    
    def _format_price(self, price: float) -> str:
        """Format price with appropriate decimal places"""
        if price == 0:
            return "0.00"
        elif price < 0.000001:
            return f"{price:.10f}"
        elif price < 0.0001:
            return f"{price:.8f}"
        elif price < 0.01:
            return f"{price:.6f}"
        elif price < 1:
            return f"{price:.4f}"
        else:
            return f"{price:.2f}"
    
    def _get_ratio_status(self, ratio: float) -> str:
        """Get status emoji and text for volume/liquidity ratio"""
        if ratio <= 5.0:
            return "✅ Ratio Ótimo"
        elif ratio <= 8.0:
            return "⚠️ Ratio Aceitável"
        else:
            return "🚨 Ratio Alto - Monitore"
    
    def _send_message(self, message: str) -> bool:
        """Send message to Telegram using Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("✅ Telegram notification sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    return False
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        if not self.enabled:
            print("❌ Telegram not configured")
            return False
        
        test_message = f"""🧪 <b>TESTE - Smart Currency Selector</b>

✅ Conexão com Telegram funcionando!
📱 Chat ID: <code>{self.chat_id}</code>
🤖 Bot configurado corretamente

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

<i>Sistema pronto para enviar notificações de tokens!</i>"""
        
        success = self._send_message(test_message)
        if success:
            print("✅ Mensagem de teste enviada com sucesso!")
        else:
            print("❌ Falha ao enviar mensagem de teste")
        
        return success
    
    def send_performance_update(self, stats: Dict) -> bool:
        """Send performance update notification"""
        if not self.enabled:
            return False
        
        try:
            win_rate = stats.get('win_rate', 0)
            total_tokens = stats.get('total_tokens', 0)
            avg_return = stats.get('average_return', 0)
            best_performer = stats.get('best_performer', {})
            
            message = f"""📊 <b>RELATÓRIO DE PERFORMANCE</b>

🎯 Taxa de Acerto: <b>{win_rate:.1f}%</b>
📈 Retorno Médio: <b>{avg_return:+.2f}%</b>
🔢 Total Analisado: {total_tokens} tokens

🏆 <b>Melhor Performance:</b>
💰 {best_performer.get('symbol', 'N/A')}: {best_performer.get('return', 0):+.1f}%

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

<i>Relatório automático do sistema</i>"""
            
            return self._send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send performance update: {e}")
            return False
    
    def send_notification(self, message: str, notification_type: str = "INFO") -> bool:
        """
        Generic notification method for trade events
        
        Args:
            message: The formatted message to send
            notification_type: Type of notification (TRADE_BUY, TRADE_SELL, INFO, ERROR)
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            # Add notification type indicator if not already in message
            if notification_type == "ERROR" and "❌" not in message:
                message = "❌ " + message
            elif notification_type == "TRADE_BUY" and "💰" not in message:
                # Message already formatted, just send it
                pass
            elif notification_type == "TRADE_SELL" and "✅" not in message and "🔴" not in message:
                # Message already formatted, just send it
                pass
            
            return self._send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send {notification_type} notification: {e}")
            return False

# Global notifier instance
telegram_notifier = TelegramNotifier()