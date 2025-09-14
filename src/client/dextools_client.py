import requests
import time
from typing import Dict, Any, List, Optional


class DEXToolsClient:
    def __init__(self, api_key: str, base_url: str, rate_limit_delay: float = 2.0):
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = rate_limit_delay
        self.headers = {
            "accept": "application/json",
            "X-API-Key": api_key
        }
        self._last_request_time = 0

    def _make_request(self, url: str) -> requests.Response:
        """Faz requisição com rate limiting"""
        # Espera o tempo necessário desde a última requisição
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"⏱️  Aguardando {sleep_time:.1f}s para evitar rate limit...")
            time.sleep(sleep_time)
        
        response = requests.get(url, headers=self.headers)
        self._last_request_time = time.time()
        return response

    def get_token_pools(self, chain: str, token_address: str) -> Optional[Dict[str, Any]]:
        """Busca pools do token e retorna a com maior liquidez"""
        url = f"{self.base_url}/token/{chain}/{token_address}/pools?sort=creationTime&order=desc&from=2020-01-01T00:00:00.000Z&to=2026-01-01T00:00:00.000Z"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            json_data = response.json()
            pools = json_data.get('data', {}).get('results', [])
            if not pools:
                return None
            # Retorna a primeira pool (mais recente por creationTime desc)
            return pools[0]
        except Exception as e:
            print(f"Erro ao buscar pools: {e}")
            return None

    def get_pool_score(self, chain: str, pool_address: str) -> Dict[str, Any]:
        """Obtém score de segurança da pool"""
        url = f"{self.base_url}/pool/{chain}/{pool_address}/score"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Erro ao buscar score da pool: {e}")
            return {"dextScore": {"total": 0}, "votes": {"upvotes": 0, "downvotes": 0}}

    def get_token_score(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Obtém score de segurança do token"""
        url = f"{self.base_url}/token/{chain}/{token_address}/score"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Erro ao buscar score do token: {e}")
            return {"dextScore": {"total": 0}, "votes": {"upvotes": 0, "downvotes": 0}}

    def get_token_locks(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Verifica se liquidez está bloqueada"""
        url = f"{self.base_url}/token/{chain}/{token_address}/locks"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Erro ao verificar locks: {e}")
            return {"hasLockedLiquidity": False}

    def get_token_audit(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Obtém dados completos de auditoria incluindo taxas de buy/sell"""
        url = f"{self.base_url}/token/{chain}/{token_address}/audit"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            data = response.json().get('data', {})
            
            # Processa dados de auditoria com foco nas taxas
            audit_info = {
                "is_open_source": data.get("isOpenSource", "unknown"),
                "is_honeypot": data.get("isHoneypot", "unknown"), 
                "is_mintable": data.get("isMintable", "unknown"),
                "is_proxy": data.get("isProxy", "unknown"),
                "slippage_modifiable": data.get("slippageModifiable", "unknown"),
                "is_blacklisted": data.get("isBlacklisted", "unknown"),
                "is_contract_renounced": data.get("isContractRenounced", "unknown"),
                "is_potentially_scam": data.get("isPotentiallyScam", "unknown"),
                "updated_at": data.get("updatedAt", ""),
                
                # Taxas de compra e venda - foco principal
                "buy_tax": {
                    "min": data.get("buyTax", {}).get("min", 0),
                    "max": data.get("buyTax", {}).get("max", 0), 
                    "status": data.get("buyTax", {}).get("status", "unknown")
                },
                "sell_tax": {
                    "min": data.get("sellTax", {}).get("min", 0),
                    "max": data.get("sellTax", {}).get("max", 0),
                    "status": data.get("sellTax", {}).get("status", "unknown")
                },
                
                # Dados originais para compatibilidade
                "raw_data": data
            }
            
            return audit_info
            
        except Exception as e:
            print(f"Erro ao verificar auditoria: {e}")
            return {
                "is_open_source": "unknown",
                "is_honeypot": "unknown",
                "is_mintable": "unknown", 
                "is_proxy": "unknown",
                "slippage_modifiable": "unknown",
                "is_blacklisted": "unknown",
                "is_contract_renounced": "unknown", 
                "is_potentially_scam": "unknown",
                "buy_tax": {"min": 0, "max": 0, "status": "unknown"},
                "sell_tax": {"min": 0, "max": 0, "status": "unknown"},
                "updated_at": "",
                "error": str(e)
            }

    def get_token_details(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Obtém detalhes básicos do token"""
        url = f"{self.base_url}/token/{chain}/{token_address}"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            print(f"Erro ao buscar detalhes do token: {e}")
            return {}

    def get_token_price_detailed(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Obtém dados detalhados de preço do token"""
        url = f"{self.base_url}/token/{chain}/{token_address}/price"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            print(f"Erro ao buscar preços detalhados: {e}")
            return {}

    def get_pool_liquidity(self, chain: str, pool_address: str) -> Dict[str, Any]:
        """Obtém dados de liquidez da pool"""
        url = f"{self.base_url}/pool/{chain}/{pool_address}/liquidity"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            print(f"Erro ao buscar liquidez da pool: {e}")
            return {}

    def get_pool_price(self, chain: str, pool_address: str) -> Dict[str, Any]:
        """Obtém dados de preço da pool"""
        url = f"{self.base_url}/pool/{chain}/{pool_address}/price"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            print(f"Erro ao buscar preço da pool: {e}")
            return {}

    def get_holders(self, chain: str, token_address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtém lista dos principais holders - usa endpoint /info como alternativa"""
        # Primeiro tenta endpoint direto de holders (pode não funcionar no plano Standard)
        url_holders = f"{self.base_url}/token/{chain}/{token_address}/holders?limit={limit}"
        try:
            response = self._make_request(url_holders)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Endpoint /holders falhou: {e}")
            # Se falhar, tenta obter dados básicos de holders do endpoint /info
            return self._get_holders_from_info(chain, token_address)
    
    def _get_holders_from_info(self, chain: str, token_address: str) -> List[Dict[str, Any]]:
        """Método alternativo para obter dados básicos de holders via /info"""
        url = f"{self.base_url}/token/{chain}/{token_address}/info"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            data = response.json().get('data', {})
            holders_count = int(data.get('holders', 0)) if str(data.get('holders', 0)).isdigit() else 0
            
            # Retorna dados simulados baseados no número total de holders
            # Não temos lista detalhada, mas temos o total
            return [{"total_holders": holders_count, "available": "count_only"}]
        except Exception as e:
            print(f"Erro ao buscar holders via info: {e}")
            return []

    def analyze_top_holders(self, chain: str, token_address: str, top_n: int = 10) -> Dict[str, Any]:
        """Analisa concentração dos principais holders"""
        holders = self.get_holders(chain, token_address, top_n)
        if not holders:
            return {"top_holders": [], "percentage": 0, "total_holders": 0}
        
        # Verifica se é resposta alternativa do /info (só com contagem)
        if len(holders) == 1 and "total_holders" in holders[0]:
            return {
                "top_holders": [],
                "percentage": 0,
                "total_holders": holders[0]["total_holders"],
                "note": "Dados detalhados de holders não disponíveis no plano Standard. Apenas contagem total."
            }
        
        # Processamento normal se temos dados detalhados
        total_supply = sum([float(h.get('balance', 0)) for h in holders])
        top_total = sum([float(h.get('balance', 0)) for h in holders[:top_n]])
        percentage = (top_total / total_supply) * 100 if total_supply else 0
        
        return {
            "top_holders": holders[:top_n],
            "percentage": round(percentage, 2),
            "total_holders": len(holders)
        }

    def get_price_metrics(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Obtém métricas completas de preço, volume e liquidez"""
        # Dados básicos do /info
        info_data = self._get_token_info(chain, token_address)
        
        # Dados detalhados de preço
        price_data = self.get_token_price_detailed(chain, token_address)
        
        # Dados básicos do token principal
        token_data = self.get_token_details(chain, token_address)
        
        # Busca pool principal e sua liquidez
        pool = self.get_token_pools(chain, token_address)
        liquidity_data = {}
        pool_price_data = {}
        
        if pool and pool.get('address'):
            liquidity_data = self.get_pool_liquidity(chain, pool['address'])
            pool_price_data = self.get_pool_price(chain, pool['address'])
        
        # Combina todos os dados
        mcap = info_data.get("mcap", 0) if isinstance(info_data, dict) else 0
        circulating_supply = info_data.get("circulatingSupply", 0) if isinstance(info_data, dict) else 0
        price_usd = mcap / circulating_supply if circulating_supply else 0
        
        # Extrai preços detalhados se disponível
        if price_data and isinstance(price_data, dict):
            price_usd = price_data.get("price", price_usd)
        
        return {
            "price_usd": price_usd,
            "price_change_24h": price_data.get("variation24h", 0) if isinstance(price_data, dict) else 0,
            "price_change_1h": price_data.get("variation1h", 0) if isinstance(price_data, dict) else 0,
            "price_change_5m": price_data.get("variation5m", 0) if isinstance(price_data, dict) else 0,
            "liquidity_usd": liquidity_data.get("liquidity", 0) if isinstance(liquidity_data, dict) else 0,
            "volume_24h_usd": pool_price_data.get("volume24h", 0) if isinstance(pool_price_data, dict) else 0,
            "volume_1h_usd": pool_price_data.get("volume1h", 0) if isinstance(pool_price_data, dict) else 0,
            "volume_6h_usd": pool_price_data.get("volume6h", 0) if isinstance(pool_price_data, dict) else 0,
            "mcap": mcap,
            "fdv": info_data.get("fdv", 0) if isinstance(info_data, dict) else 0,
            "circulating_supply": circulating_supply,
            "total_supply": info_data.get("totalSupply", 0) if isinstance(info_data, dict) else 0,
            "holders_count": int(info_data.get("holders", 0)) if isinstance(info_data, dict) and str(info_data.get("holders", 0)).isdigit() else 0,
            "transactions": info_data.get("transactions", 0) if isinstance(info_data, dict) else 0,
            "token_name": token_data.get("name", "") if isinstance(token_data, dict) else "",
            "token_symbol": token_data.get("symbol", "") if isinstance(token_data, dict) else "",
            "dex_info": pool.get("exchange", {}) if pool and isinstance(pool, dict) else {},
            "pool_address": pool.get("address", "") if pool and isinstance(pool, dict) else ""
        }
    
    def _get_token_info(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Método auxiliar para buscar dados do endpoint /info"""
        url = f"{self.base_url}/token/{chain}/{token_address}/info"
        try:
            response = self._make_request(url)
            response.raise_for_status()
            return response.json().get('data', {})
        except Exception as e:
            print(f"Erro ao buscar info do token: {e}")
            return {}

    def _safe_get_nested(self, data: Any, key1: str, key2: str, default: Any = 0) -> Any:
        """Método auxiliar para acessar dados aninhados com segurança"""
        if not isinstance(data, dict):
            return default
        
        nested = data.get(key1)
        if not isinstance(nested, dict):
            return default
        
        return nested.get(key2, default)

    def get_price_trend(self, chain: str, token_address: str) -> str:
        """Analisa tendência de preço baseado nos dados disponíveis"""
        # Tenta obter dados detalhados de preço
        price_data = self.get_token_price_detailed(chain, token_address)
        
        if not price_data:
            return "❌ Dados de preço não disponíveis"
        
        # Analisa baseado nas variações percentuais (usando variation* ao invés de change*)
        change_5m = price_data.get("variation5m", 0)
        change_1h = price_data.get("variation1h", 0) 
        change_24h = price_data.get("variation24h", 0)
        
        # Se temos dados de variação, usa eles para determinar tendência
        if any([change_5m, change_1h, change_24h]):
            if change_24h > 5:
                return f"📈 Forte alta (+{change_24h:.2f}% 24h)"
            elif change_24h > 0:
                return f"📈 Alta moderada (+{change_24h:.2f}% 24h)"
            elif change_24h < -5:
                return f"📉 Forte queda ({change_24h:.2f}% 24h)"
            elif change_24h < 0:
                return f"📉 Queda moderada ({change_24h:.2f}% 24h)"
            else:
                return f"🔄 Lateral ({change_24h:.2f}% 24h)"
        
        # Fallback para análise básica
        current_price = price_data.get("price", 0)
        if current_price > 0:
            return f"📊 Preço atual: ${current_price:.8f}"
        
        return "❌ Dados insuficientes para análise de tendência"

    def analyze_token_taxes(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Analisa detalhadamente as taxas de compra e venda do token"""
        audit_data = self.get_token_audit(chain, token_address)
        
        buy_tax = audit_data.get("buy_tax", {})
        sell_tax = audit_data.get("sell_tax", {})
        
        analysis = {
            "buy_tax_info": {
                "min_percent": buy_tax.get("min", 0),
                "max_percent": buy_tax.get("max", 0),
                "status": buy_tax.get("status", "unknown"),
                "assessment": self._assess_tax_level(buy_tax.get("max", 0), "buy")
            },
            "sell_tax_info": {
                "min_percent": sell_tax.get("min", 0), 
                "max_percent": sell_tax.get("max", 0),
                "status": sell_tax.get("status", "unknown"),
                "assessment": self._assess_tax_level(sell_tax.get("max", 0), "sell")
            },
            "overall_assessment": self._assess_overall_taxes(buy_tax.get("max", 0), sell_tax.get("max", 0)),
            "is_honeypot": audit_data.get("is_honeypot", "unknown"),
            "slippage_modifiable": audit_data.get("slippage_modifiable", "unknown"),
            "contract_renounced": audit_data.get("is_contract_renounced", "unknown"),
            "audit_date": audit_data.get("updated_at", "")
        }
        
        return analysis
    
    def _assess_tax_level(self, tax_percent, tax_type: str) -> str:
        """Avalia o nível de risco das taxas"""
        if tax_percent is None or tax_percent == 0:
            return f"✅ Sem taxa de {tax_type} (0%)"
        elif tax_percent <= 1:
            return f"✅ Taxa baixa de {tax_type} ({tax_percent}%)"
        elif tax_percent <= 5:
            return f"⚠️ Taxa moderada de {tax_type} ({tax_percent}%)"
        elif tax_percent <= 10:
            return f"🔶 Taxa alta de {tax_type} ({tax_percent}%)"
        elif tax_percent <= 25:
            return f"🚨 Taxa muito alta de {tax_type} ({tax_percent}%)"
        else:
            return f"☠️ Taxa extrema de {tax_type} ({tax_percent}%) - SUSPEITO!"
    
    def _assess_overall_taxes(self, buy_tax, sell_tax) -> str:
        """Avaliação geral das taxas combinadas"""
        buy_tax = buy_tax or 0
        sell_tax = sell_tax or 0
        total_tax = buy_tax + sell_tax
        
        if total_tax == 0:
            return "✅ Token sem taxas - Excelente para trading"
        elif total_tax <= 2:
            return f"✅ Taxas baixas ({total_tax}% total) - Bom para trading"  
        elif total_tax <= 10:
            return f"⚠️ Taxas moderadas ({total_tax}% total) - Aceitável"
        elif total_tax <= 20:
            return f"🔶 Taxas altas ({total_tax}% total) - Cuidado ao tradear"
        elif total_tax <= 50:
            return f"🚨 Taxas muito altas ({total_tax}% total) - Muito arriscado"
        else:
            return f"☠️ Taxas extremas ({total_tax}% total) - POSSÍVEL SCAM!"

    def security_check(self, chain: str, token_address: str) -> List[str]:
        """Executa verificação completa de segurança com detalhes específicos"""
        issues = []
        
        # Busca a melhor pool
        pool = self.get_token_pools(chain, token_address)
        if not pool:
            return ["❌ Nenhuma pool encontrada para este token."]
        
        pool_address = pool['address']
        
        # Verifica scores do token e da pool
        token_score_data = self.get_token_score(chain, token_address)
        pool_score_data = self.get_pool_score(chain, pool_address)
        
        # Extrai scores corretamente da estrutura da API
        token_score = token_score_data.get("dextScore", {}).get("total", 0)
        pool_score = pool_score_data.get("dextScore", {}).get("total", 0)
        
        # Votos da comunidade
        token_upvotes = token_score_data.get("votes", {}).get("upvotes", 0)
        token_downvotes = token_score_data.get("votes", {}).get("downvotes", 0)
        
        # Análise do score do token
        if token_score == 0:
            issues.append(f"🔍 Token Score: {token_score}/100 (sem dados suficientes)")
        elif token_score < 30:
            issues.append(f"🚨 Token Score: {token_score}/100 — Risco MUITO ALTO")
        elif token_score < 60:
            issues.append(f"⚠️ Token Score: {token_score}/100 — Risco elevado")
        elif token_score < 80:
            issues.append(f"📊 Token Score: {token_score}/100 — Risco moderado")
        else:
            issues.append(f"✅ Token Score: {token_score}/100 — Boa reputação")
        
        # Análise do score da pool
        if pool_score != token_score:  # Só mostra se for diferente
            if pool_score == 0:
                issues.append(f"🔍 Pool Score: {pool_score}/100 (sem dados suficientes)")
            elif pool_score < 30:
                issues.append(f"🚨 Pool Score: {pool_score}/100 — Risco MUITO ALTO")
            elif pool_score < 60:
                issues.append(f"⚠️ Pool Score: {pool_score}/100 — Risco elevado")
            elif pool_score < 80:
                issues.append(f"📊 Pool Score: {pool_score}/100 — Risco moderado")
            else:
                issues.append(f"✅ Pool Score: {pool_score}/100 — Boa reputação")
        
        # Votos da comunidade
        if token_upvotes > 0 or token_downvotes > 0:
            total_votes = token_upvotes + token_downvotes
            upvote_percent = (token_upvotes / total_votes * 100) if total_votes > 0 else 0
            issues.append(f"🗳️ Votos: {token_upvotes}👍 {token_downvotes}👎 ({upvote_percent:.1f}% positivos)")
        
        # Verifica liquidez bloqueada com detalhes
        locks_data = self.get_token_locks(chain, token_address)
        has_locked = locks_data.get("hasLockedLiquidity", False)
        
        if has_locked:
            # Se tem lock, mostra detalhes
            lock_percentage = locks_data.get("lockPercentage", 0)
            lock_end = locks_data.get("lockEnd", "N/A")
            issues.append(f"🔒 Liquidez bloqueada: {lock_percentage}% até {lock_end}")
        else:
            issues.append("🔓 Liquidez NÃO bloqueada — RISCO DE RUG PULL!")
        
        # Verifica auditoria com detalhes
        audit_data = self.get_token_audit(chain, token_address)
        is_audited = audit_data.get("audited", False)
        
        if is_audited:
            auditor = audit_data.get("auditor", "N/A")
            audit_date = audit_data.get("auditDate", "N/A")
            issues.append(f"✅ Token auditado por {auditor} em {audit_date}")
        else:
            issues.append("🕵️‍♂️ Token SEM AUDITORIA — Cuidado com contratos maliciosos!")
        
        # Verifica concentração de holders
        holders_analysis = self.analyze_top_holders(chain, token_address)
        concentration = holders_analysis.get("percentage", 0)
        total_holders = holders_analysis.get("total_holders", 0)
        
        # Análise detalhada de concentração
        if concentration == 0 and total_holders > 0:
            issues.append(f"👥 Total holders: {total_holders} (dados detalhados não disponíveis)")
        elif concentration > 70:
            issues.append(f"🚨 ALTA concentração: Top 10 holders = {concentration}% — RISCO de manipulação!")
        elif concentration > 50:
            issues.append(f"⚠️ Concentração moderada: Top 10 holders = {concentration}%")
        elif concentration > 0:
            issues.append(f"✅ Distribuição saudável: Top 10 holders = {concentration}%")
        else:
            issues.append(f"👥 Total holders: {total_holders}")
        
        # Análise do token baseado nos dados gerais
        token_info = self._get_token_info(chain, token_address)
        transactions = token_info.get("transactions", 0)
        
        if transactions == 0:
            issues.append("⚠️ Token com ZERO transações — pode ser inativo ou muito novo")
        elif transactions < 100:
            issues.append(f"⚠️ Poucas transações ({transactions}) — baixa atividade")
        else:
            issues.append(f"✅ Atividade normal ({transactions} transações)")
        
        return issues

    def complete_analysis(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Executa análise completa do token"""
        print(f"\n🔍 Analisando token: {token_address}")
        print("=" * 50)
        
        # Verificação de segurança
        print("\n🛡️ VERIFICAÇÃO DE SEGURANÇA:")
        security_issues = self.security_check(chain, token_address)
        for issue in security_issues:
            print(f"  {issue}")
        
        # Métricas de preço
        print("\n📊 MÉTRICAS DO TOKEN:")
        metrics = self.get_price_metrics(chain, token_address)
        print(f"  Preço (USD): ${metrics['price_usd']:.8f}")
        print(f"  Variação 24h: {metrics['price_change_24h']:.2f}%")
        print(f"  Liquidez: ${metrics['liquidity_usd']:,.2f}")
        print(f"  Volume 24h: ${metrics['volume_24h_usd']:,.2f}")
        
        # Tendência de preço
        print("\n📈 TENDÊNCIA DE PREÇO:")
        trend = self.get_price_trend(chain, token_address)
        print(f"  {trend}")
        
        # Análise de holders
        print("\n👑 ANÁLISE DOS TOP HOLDERS:")
        holders = self.analyze_top_holders(chain, token_address)
        print(f"  Top 10 holders detêm {holders['percentage']:.2f}% do supply total")
        
        # Análise de taxas e auditoria
        print("\n💸 ANÁLISE DE TAXAS:")
        tax_analysis = self.analyze_token_taxes(chain, token_address)
        
        buy_info = tax_analysis.get('buy_tax_info', {})
        sell_info = tax_analysis.get('sell_tax_info', {})
        
        print(f"  📈 Taxa de Compra: {buy_info.get('min_percent', 0)}% - {buy_info.get('max_percent', 0)}%")
        print(f"  📉 Taxa de Venda: {sell_info.get('min_percent', 0)}% - {sell_info.get('max_percent', 0)}%")
        print(f"  ⚖️ Avaliação: {tax_analysis.get('overall_assessment', 'N/A')}")
        
        # Informações de auditoria
        print("\n🔍 AUDITORIA DE SEGURANÇA:")
        print(f"  🍯 Honeypot: {tax_analysis.get('is_honeypot', 'N/A')}")
        print(f"  🔐 Contrato Renunciado: {tax_analysis.get('contract_renounced', 'N/A')}")
        print(f"  📊 Slippage Modificável: {tax_analysis.get('slippage_modifiable', 'N/A')}")
        
        print("\n📋 TOP 10 HOLDERS:")
        for i, holder in enumerate(holders['top_holders'][:10], 1):
            balance = float(holder.get('balance', 0))
            print(f"  {i:2d}. {holder.get('address', 'N/A')[:42]} — {balance:,.2f}")
        
        return {
            "security_issues": security_issues,
            "metrics": metrics,
            "trend": trend,
            "holders": holders,
            "tax_analysis": tax_analysis
        }