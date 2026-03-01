# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — DCR (Displaced Commercial Risk) Motoru
IFSB ve AAOIFI standartlarında en çok tartışılan katılım bankası riski.

DCR: Bankanın rekabetçi kalabilmek için kendi kârından feragat etme riski.
- Piyasa oranları yüksekken, banka müşterisine aynı oranı vermek zorundadır
- Aksi halde müşteri başka bankaya geçer
- Banka bu farkı PER (Profit Equalization Reserve) ve IRR (Investment Risk Reserve) ile yönetir
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict
from models import BalanceSheetItem, ProfitPool, DCRResult
import config


def calculate_dcr(
    pools: List[ProfitPool],
    market_benchmark_rate: float = None,
    equity: float = None,
) -> DCRResult:
    """
    Displaced Commercial Risk hesaplar.
    
    DCR ortaya çıkar eğer:
    - Bankanın sunduğu kâr payı oranı < piyasa benchmark oranı
    - Banka, müşteri kaybetmemek için kendi payından (alpha) feragat eder
    
    Args:
        pools: Kâr payı havuzları
        market_benchmark_rate: Piyasa referans kâr payı oranı
        equity: Toplam özkaynaklar
    """
    if market_benchmark_rate is None:
        market_benchmark_rate = config.DEFAULT_PROFIT_RATE
    
    if not pools:
        return DCRResult()
    
    # Bankanın ağırlıklı ortalama müşteri kâr payı oranı
    total_funds = sum(p.total_funds for p in pools)
    if total_funds == 0:
        return DCRResult()
    
    offered_rate = sum(
        p.profit_rate * p.total_funds for p in pools
    ) / total_funds
    
    # DCR Spread
    spread = market_benchmark_rate - offered_rate
    
    # DCR maruz kalım tutarı
    dcr_exposure = 0.0
    if spread > config.DCR_PARAMS["market_benchmark_spread"]:
        dcr_exposure = total_funds * spread  # Yıllık potansiyel kayıp
    
    # PER ve IRR hesaplama
    total_income = sum(p.gross_income for p in pools) * 12  # Yıllık
    per_contribution = total_income * config.DCR_PARAMS["per_rate"]
    irr_contribution = total_income * config.DCR_PARAMS["irr_rate"]
    
    # PER ve IRR bakiye (birikmiş)
    per_balance = per_contribution * 3  # 3 yıllık birikim varsayımı
    irr_balance = irr_contribution * 3
    
    # PER max kontrolü
    per_max = total_funds * config.DCR_PARAMS["per_max_ratio"]
    per_balance = min(per_balance, per_max)
    
    irr_max = total_funds * config.DCR_PARAMS["irr_max_ratio"]
    irr_balance = min(irr_balance, irr_max)
    
    # Mevcut alpha ve gereken alpha
    alpha_current = sum(p.bank_share_ratio * p.total_funds for p in pools) / total_funds
    
    # DCR'yi karşılamak için gereken alpha (feragat edilecek oran)
    alpha_required = alpha_current
    if spread > 0:
        # Farkı kapatmak için banka payından ne kadar verilmeli?
        total_net_income = sum(p.net_income for p in pools) * 12
        if total_net_income > 0:
            alpha_required = max(
                config.DCR_PARAMS["alpha_min"],
                alpha_current - (dcr_exposure / total_net_income) * alpha_current
            )
    
    # DCR riski var mı?
    is_dcr_risk = spread > config.DCR_PARAMS["market_benchmark_spread"]
    
    # Özkaynak etkisi
    dcr_equity_impact = 0.0
    if equity and equity > 0 and is_dcr_risk:
        dcr_equity_impact = (dcr_exposure / equity) * 100
    
    return DCRResult(
        market_benchmark_rate=round(market_benchmark_rate, 4),
        offered_rate=round(offered_rate, 4),
        spread=round(spread, 4),
        dcr_exposure=round(dcr_exposure, 2),
        per_balance=round(per_balance, 2),
        irr_balance=round(irr_balance, 2),
        per_contribution=round(per_contribution, 2),
        irr_contribution=round(irr_contribution, 2),
        alpha_current=round(alpha_current, 4),
        alpha_required=round(alpha_required, 4),
        is_dcr_risk=is_dcr_risk,
        dcr_impact_on_equity=round(dcr_equity_impact, 2),
    )


def dcr_sensitivity_analysis(
    pools: List[ProfitPool],
    equity: float,
    benchmark_range: List[float] = None,
) -> List[Dict]:
    """
    DCR hassasiyet analizi — farklı piyasa oranlarında DCR etkisi.
    
    Args:
        benchmark_range: Test edilecek piyasa oranları
    """
    if benchmark_range is None:
        base = config.DEFAULT_PROFIT_RATE
        benchmark_range = [
            base - 0.10, base - 0.05, base,
            base + 0.05, base + 0.10, base + 0.15,
        ]
    
    results = []
    for rate in benchmark_range:
        dcr = calculate_dcr(pools, rate, equity)
        results.append({
            "benchmark_rate": round(rate * 100, 2),
            "offered_rate": round(dcr.offered_rate * 100, 2),
            "spread_bp": round(dcr.spread * 10000),
            "dcr_exposure": dcr.dcr_exposure,
            "alpha_required": round(dcr.alpha_required, 4),
            "is_risk": dcr.is_dcr_risk,
            "equity_impact_pct": dcr.dcr_impact_on_equity,
        })
    
    return results


def per_irr_adequacy(
    dcr_result: DCRResult,
) -> Dict:
    """
    PER ve IRR yeterliliğini değerlendirir.
    
    Returns:
        dict: Yeterlilik durumu ve öneriler
    """
    coverage_ratio = 0.0
    if dcr_result.dcr_exposure > 0:
        total_reserves = dcr_result.per_balance + dcr_result.irr_balance
        coverage_ratio = (total_reserves / dcr_result.dcr_exposure) * 100
    
    status = "yeşil"  # Güvenli
    recommendation = "DCR riski kontrol altında."
    
    if dcr_result.is_dcr_risk:
        if coverage_ratio < 50:
            status = "kırmızı"
            recommendation = "PER/IRR yetersiz! Reserve artırılmalı veya alpha düşürülmeli."
        elif coverage_ratio < 80:
            status = "sarı"
            recommendation = "PER/IRR yeterliliği dikkat gerektiriyor. Reserve artırımı değerlendirilmeli."
        else:
            status = "yeşil"
            recommendation = "PER/IRR yeterli seviyede. Mevcut politika sürdürülebilir."
    
    return {
        "coverage_ratio": round(coverage_ratio, 2),
        "status": status,
        "recommendation": recommendation,
        "per_balance": dcr_result.per_balance,
        "irr_balance": dcr_result.irr_balance,
        "total_reserves": dcr_result.per_balance + dcr_result.irr_balance,
        "dcr_exposure": dcr_result.dcr_exposure,
    }
