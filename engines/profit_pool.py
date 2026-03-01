# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Kâr Payı Havuzu Yönetimi (Profit Pool Management)
Katılım bankalarına özgü en önemli modül. Konvansiyonel bankalarda karşılığı yok.

Katılım bankaları:
- Farklı vade havuzları oluşturur (1 ay, 3 ay, 6 ay, 1 yıl, 1 yıl+)
- Her havuzun kârını ayrı hesaplar
- Müşteriye dağıtılan kâr payı havuz performansına bağlıdır
- Pool Transfer Pricing ile havuzlar arası kaynak aktarımı yapılır
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict
from models import BalanceSheetItem, ProfitPool, ProfitPoolResult
import config


def calculate_pool_income(
    pool_funds: float,
    placements: List[BalanceSheetItem],
    alpha: float = None,
) -> ProfitPool:
    """
    Tek bir havuzun kâr payı dağıtımını hesaplar.
    
    Gelir = Kullandırılan tutar × ağırlıklı ortalama kâr payı oranı
    Banka Payı = Gelir × alpha
    Müşteri Payı = Gelir × (1 - alpha)
    """
    if alpha is None:
        alpha = config.DCR_PARAMS["alpha_default"]
    
    total_placements = sum(p.amount for p in placements)
    
    if total_placements == 0:
        return ProfitPool(total_funds=pool_funds)
    
    # Ağırlıklı ortalama getiri
    weighted_rate = sum(
        p.amount * p.profit_rate for p in placements
    ) / total_placements if total_placements > 0 else 0
    
    # Brüt gelir (aylık)
    gross_income = total_placements * weighted_rate / 12
    
    # Operasyonel gider (%3-5 aralığında sabit)
    expenses = gross_income * 0.05
    net_income = gross_income - expenses
    
    # Kâr dağıtımı
    bank_income = net_income * alpha
    customer_income = net_income * (1 - alpha)
    
    # Müşteriye dağıtılan kâr payı oranı (yıllıklandırılmış)
    customer_rate = (customer_income * 12) / pool_funds if pool_funds > 0 else 0
    
    # Fon kullanım oranı
    utilization = (total_placements / pool_funds * 100) if pool_funds > 0 else 0
    
    return ProfitPool(
        total_funds=pool_funds,
        total_placements=total_placements,
        gross_income=round(gross_income, 2),
        expenses=round(expenses, 2),
        net_income=round(net_income, 2),
        bank_share_ratio=alpha,
        customer_share_ratio=1 - alpha,
        bank_income=round(bank_income, 2),
        customer_income=round(customer_income, 2),
        profit_rate=round(customer_rate, 4),
        fund_utilization=round(utilization, 2),
    )


def calculate_all_pools(
    balance_sheet: List[BalanceSheetItem],
    alpha_by_tenor: Dict[str, float] = None,
) -> ProfitPoolResult:
    """
    Tüm kâr payı havuzlarını hesaplar.
    
    Args:
        balance_sheet: Bilanço kalemleri
        alpha_by_tenor: Vade bazlı alpha oranları
            Ör: {"1_ay": 0.45, "3_ay": 0.50, "6_ay": 0.55, ...}
    """
    if alpha_by_tenor is None:
        alpha_by_tenor = {}
    
    pools = []
    total_funds = 0.0
    total_income = 0.0
    total_bank = 0.0
    total_customer = 0.0
    
    # Aktif taraf (plasmanlar) — havuzlara dağıtılacak
    aktifler = [i for i in balance_sheet if i.side == "aktif" and i.profit_rate > 0]
    
    for tenor_key, tenor_info in config.PROFIT_POOL_TENORS.items():
        # Bu vade grubundaki katılma hesapları (fon kaynağı)
        pool_deposits = [
            i for i in balance_sheet
            if i.side == "pasif"
            and "katilma" in i.instrument_type
            and tenor_info["min_days"] <= i.maturity_days <= tenor_info["max_days"]
        ]
        
        pool_fund = sum(i.amount for i in pool_deposits)
        if pool_fund == 0:
            continue
        
        # Bu havuza uygun plasmanları belirle (basitleştirilmiş: vade eşleştirme)
        pool_placements = [
            i for i in aktifler
            if tenor_info["min_days"] <= i.maturity_days <= tenor_info["max_days"] * 1.5
        ]
        
        # Plasmanları fon miktarıyla orantılı olarak ata
        total_placement_available = sum(p.amount for p in pool_placements)
        if total_placement_available > pool_fund:
            # Plasmanları fon oranında kes
            ratio = pool_fund / total_placement_available
            scaled_placements = []
            for p in pool_placements:
                scaled = BalanceSheetItem(
                    name=p.name,
                    amount=p.amount * ratio,
                    side=p.side,
                    instrument_type=p.instrument_type,
                    profit_rate=p.profit_rate,
                    maturity_days=p.maturity_days,
                )
                scaled_placements.append(scaled)
            pool_placements = scaled_placements
        
        alpha = alpha_by_tenor.get(tenor_key, config.DCR_PARAMS["alpha_default"])
        
        pool = calculate_pool_income(pool_fund, pool_placements, alpha)
        pool.pool_name = f"{tenor_info['label']} Havuzu"
        pool.tenor = tenor_key
        
        pools.append(pool)
        total_funds += pool.total_funds
        total_income += pool.net_income
        total_bank += pool.bank_income
        total_customer += pool.customer_income
    
    # Ağırlıklı ortalama kâr payı
    weighted_avg_rate = (
        sum(p.profit_rate * p.total_funds for p in pools) / total_funds
        if total_funds > 0 else 0
    )
    
    return ProfitPoolResult(
        pools=pools,
        total_funds=round(total_funds, 2),
        total_income=round(total_income, 2),
        weighted_avg_rate=round(weighted_avg_rate, 4),
        total_bank_share=round(total_bank, 2),
        total_customer_share=round(total_customer, 2),
    )


def pool_transfer_pricing(
    pools: List[ProfitPool],
    internal_rate: float = None,
) -> List[Dict]:
    """
    Havuzlar arası kaynak aktarımı (Pool Transfer Pricing) hesaplar.
    
    Fazla fonu olan havuz → eksik fonu olan havuza aktarım yapar.
    İç transfer fiyatı (internal_rate) ile fiyatlandırılır.
    
    Returns:
        list[dict]: Transfer detayları
    """
    if internal_rate is None:
        internal_rate = config.DEFAULT_PROFIT_RATE * 0.8  # İç oran ≈ piyasa oranının %80'i
    
    transfers = []
    
    # Fazla / eksik fon hesapla
    for pool in pools:
        surplus = pool.total_funds - pool.total_placements
        
        if surplus > 0:
            # Fazla fonu var → başka havuza aktarabilir
            transfer_income = surplus * internal_rate / 12  # Aylık
            transfers.append({
                "pool": pool.pool_name,
                "type": "fazla",
                "amount": surplus,
                "internal_rate": internal_rate,
                "transfer_income": transfer_income,
            })
        elif surplus < 0:
            # Eksik fon → başka havuzdan alabilir
            transfer_cost = abs(surplus) * internal_rate / 12
            transfers.append({
                "pool": pool.pool_name,
                "type": "eksik",
                "amount": abs(surplus),
                "internal_rate": internal_rate,
                "transfer_cost": transfer_cost,
            })
    
    return transfers
