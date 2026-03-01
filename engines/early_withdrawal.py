# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Erken Çekim Riski (Early Withdrawal Risk) Motoru
Vadeli katılma hesaplarından vade sonundan önce para çekilme riski.

Katılım bankalarında erken çekim:
- Konvansiyonel bankalarda ceza uygulanır
- Katılım bankalarında kâr payı kaybedilir / azaltılır
- Ama anapara her zaman korunur (TMSF garantisi)
- Bu nedenle erken çekim olasılığı daha yüksek olabilir
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict
from models import BalanceSheetItem, EarlyWithdrawalResult
import config


def calculate_early_withdrawal_risk(
    balance_sheet: List[BalanceSheetItem],
    stress_level: str = None,
    rate_change_bp: int = 0,
) -> List[EarlyWithdrawalResult]:
    """
    Vade bazlı erken çekim riski hesaplar.
    
    Args:
        balance_sheet: Bilanço kalemleri
        stress_level: "hafif", "orta", "siddetli" veya None (baz durum)
        rate_change_bp: Kâr payı oranı değişimi (baz puan, + = artış)
    """
    results = []
    
    for tenor_key, tenor_info in config.PROFIT_POOL_TENORS.items():
        # Bu vade grubundaki vadeli katılma hesapları
        deposits = [
            i for i in balance_sheet
            if i.side == "pasif"
            and "katilma_vadeli" in i.instrument_type
            and tenor_info["min_days"] <= i.maturity_days <= tenor_info["max_days"]
        ]
        
        total = sum(i.amount for i in deposits)
        if total == 0:
            continue
        
        # Baz erken çekim olasılığı
        base_prob = config.EARLY_WITHDRAWAL_PARAMS["base_probability"].get(
            tenor_key, 0.05
        )
        
        # Kâr payı oranı değişimine hassasiyet
        # Piyasa oranları yükselirse → erken çekim artar (müşteri daha iyi oran arar)
        rate_adj = 0.0
        if rate_change_bp > 0:
            # Oranlar yükseldiğinde çekim artar
            rate_adj = (rate_change_bp / 10000) * config.EARLY_WITHDRAWAL_PARAMS["rate_sensitivity"]
        
        # Stres çarpanı
        stress_mult = 1.0
        if stress_level:
            stress_mult = config.EARLY_WITHDRAWAL_PARAMS["stress_multiplier"].get(
                stress_level, 1.0
            )
        
        # Nihai olasılık
        stressed_prob = min(1.0, (base_prob + rate_adj) * stress_mult)
        
        # Beklenen çekim tutarları
        expected = total * base_prob
        stressed = total * stressed_prob
        
        # LCR etkisi (30 günlük pencerede)
        lcr_impact = stressed - expected
        
        deposit_details = [
            {"name": d.name, "amount": d.amount, "maturity_days": d.maturity_days}
            for d in deposits
        ]
        
        results.append(EarlyWithdrawalResult(
            tenor=tenor_info["label"],
            total_deposits=total,
            base_withdrawal_prob=round(base_prob, 4),
            stressed_withdrawal_prob=round(stressed_prob, 4),
            expected_withdrawal=round(expected, 2),
            stressed_withdrawal=round(stressed, 2),
            lcr_impact=round(lcr_impact, 2),
            items=deposit_details,
        ))
    
    return results


def get_early_withdrawal_summary(
    results: List[EarlyWithdrawalResult],
) -> Dict:
    """Erken çekim riski özeti."""
    total_deposits = sum(r.total_deposits for r in results)
    total_expected = sum(r.expected_withdrawal for r in results)
    total_stressed = sum(r.stressed_withdrawal for r in results)
    total_lcr_impact = sum(r.lcr_impact for r in results)
    
    # En riskli vade grubu
    highest_risk = max(results, key=lambda r: r.stressed_withdrawal_prob) if results else None
    
    return {
        "total_term_deposits": total_deposits,
        "total_expected_withdrawal": total_expected,
        "total_stressed_withdrawal": total_stressed,
        "total_lcr_impact": total_lcr_impact,
        "avg_base_probability": (
            sum(r.base_withdrawal_prob * r.total_deposits for r in results) / total_deposits
            if total_deposits > 0 else 0
        ),
        "highest_risk_tenor": highest_risk.tenor if highest_risk else "",
        "highest_risk_prob": highest_risk.stressed_withdrawal_prob if highest_risk else 0,
    }
