# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Bilanço Dışı Kalemler Motoru
Gayrinakdi krediler, Wa'd/Muwa'ada taahhütleri, LCR/NSFR etkisi.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict
from models import OffBalanceSheetItem
import config


def calculate_obs_lcr_impact(
    off_balance: List[OffBalanceSheetItem],
) -> Dict:
    """
    Bilanço dışı kalemlerin LCR nakit çıkışı etkisini hesaplar.
    
    Returns:
        dict: Toplam etki ve kalem bazlı detay
    """
    total_outflow = 0.0
    details = []
    
    for item in off_balance:
        # Runoff rate (LCR için)
        runoff = config.RUNOFF_RATES.get(item.item_type, 0.05)
        outflow = item.amount * runoff
        
        details.append({
            "name": item.name,
            "amount": item.amount,
            "item_type": item.item_type,
            "runoff_rate": runoff,
            "outflow": outflow,
            "currency": item.currency,
            "counterparty_type": item.counterparty_type,
        })
        total_outflow += outflow
    
    return {
        "total_outflow": total_outflow,
        "details": details,
        "item_count": len(off_balance),
        "total_nominal": sum(i.amount for i in off_balance),
    }


def calculate_obs_leverage_exposure(
    off_balance: List[OffBalanceSheetItem],
) -> Dict:
    """
    Bilanço dışı kalemlerin kaldıraç oranı risk tutarını hesaplar.
    CCF (Credit Conversion Factor) uygulanır.
    """
    total_exposure = 0.0
    details = []
    
    for item in off_balance:
        ccf = item.ccf if item.ccf > 0 else config.OFF_BALANCE_CCF.get(item.item_type, 0.10)
        exposure = item.amount * ccf
        
        details.append({
            "name": item.name,
            "nominal": item.amount,
            "ccf": ccf,
            "exposure": exposure,
            "item_type": item.item_type,
        })
        total_exposure += exposure
    
    return {
        "total_exposure": total_exposure,
        "details": details,
        "total_nominal": sum(i.amount for i in off_balance),
    }


def classify_obs_items(
    off_balance: List[OffBalanceSheetItem],
) -> Dict:
    """
    Bilanço dışı kalemleri türlerine göre sınıflandırır ve özetler.
    """
    categories = {}
    
    for item in off_balance:
        cat = item.item_type
        if cat not in categories:
            categories[cat] = {
                "count": 0,
                "total_amount": 0.0,
                "items": [],
            }
        categories[cat]["count"] += 1
        categories[cat]["total_amount"] += item.amount
        categories[cat]["items"].append(item.name)
    
    return categories


def get_obs_summary(off_balance: List[OffBalanceSheetItem]) -> Dict:
    """Bilanço dışı kalemler özet rapor."""
    if not off_balance:
        return {"total_nominal": 0, "categories": {}, "lcr_impact": 0, "leverage_exposure": 0}
    
    lcr = calculate_obs_lcr_impact(off_balance)
    leverage = calculate_obs_leverage_exposure(off_balance)
    categories = classify_obs_items(off_balance)
    
    return {
        "total_nominal": sum(i.amount for i in off_balance),
        "categories": categories,
        "lcr_outflow_impact": lcr["total_outflow"],
        "leverage_exposure": leverage["total_exposure"],
        "item_count": len(off_balance),
    }
