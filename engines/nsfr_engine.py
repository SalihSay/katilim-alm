# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — NSFR (Net Stabil Fonlama Oranı) Hesaplama Motoru
Basel III / BDDK düzenlemesine uygun NSFR hesaplama.

NSFR = Available Stable Funding (ASF) / Required Stable Funding (RSF) × 100
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from models import BalanceSheetItem, OffBalanceSheetItem, ASFBreakdown, RSFBreakdown, NSFRResult
from engines.katilim_mapping import get_asf_weight, get_rsf_weight
import config


def calculate_asf(liabilities: List[BalanceSheetItem]) -> ASFBreakdown:
    """
    Available Stable Funding (ASF) hesaplar.
    Her pasif kalemini vade ve türüne göre ağırlıklandırır.
    
    ASF = Σ (Pasif kalemi × ASF ağırlığı)
    """
    result = ASFBreakdown()
    
    for item in liabilities:
        if item.side != "pasif":
            continue
        
        weight = get_asf_weight(item)
        contribution = item.amount * weight
        
        result.items_detail.append({
            "name": item.name,
            "amount": item.amount,
            "weight": weight,
            "contribution": contribution,
            "instrument_type": item.instrument_type,
            "maturity_days": item.maturity_days,
            "currency": item.currency,
        })
        
        result.total_asf += contribution
    
    return result


def calculate_rsf(
    assets: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
) -> RSFBreakdown:
    """
    Required Stable Funding (RSF) hesaplar.
    Her aktif kalemini vade ve türüne göre ağırlıklandırır.
    
    RSF = Σ (Aktif kalemi × RSF ağırlığı) + Σ (Bilanço dışı × RSF ağırlığı)
    """
    result = RSFBreakdown()
    
    # Bilanço içi aktifler
    for item in assets:
        if item.side != "aktif":
            continue
        
        weight = get_rsf_weight(item)
        contribution = item.amount * weight
        
        result.items_detail.append({
            "name": item.name,
            "amount": item.amount,
            "weight": weight,
            "contribution": contribution,
            "instrument_type": item.instrument_type,
            "maturity_days": item.maturity_days,
            "currency": item.currency,
            "source": "bilanço_içi",
        })
        
        result.total_rsf += contribution
    
    # Bilanço dışı kalemler (düşük RSF ağırlığı)
    if off_balance:
        rsf_weight = config.RSF_WEIGHTS.get("gayrinakdi_rsf", 0.05)
        for item in off_balance:
            contribution = item.amount * rsf_weight
            
            result.items_detail.append({
                "name": item.name,
                "amount": item.amount,
                "weight": rsf_weight,
                "contribution": contribution,
                "instrument_type": item.item_type,
                "maturity_days": item.maturity_days,
                "currency": item.currency,
                "source": "bilanço_dışı",
            })
            
            result.total_rsf += contribution
    
    return result


def calculate_nsfr(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
) -> NSFRResult:
    """
    NSFR (Net Stabil Fonlama Oranı) hesaplar.
    
    NSFR = ASF / RSF × 100
    Minimum: %100 (BDDK)
    """
    pasifler = [i for i in balance_sheet if i.side == "pasif"]
    aktifler = [i for i in balance_sheet if i.side == "aktif"]
    
    asf = calculate_asf(pasifler)
    rsf = calculate_rsf(aktifler, off_balance)
    
    if rsf.total_rsf > 0:
        nsfr_ratio = (asf.total_asf / rsf.total_rsf) * 100
    else:
        nsfr_ratio = 999.99
    
    return NSFRResult(
        asf=asf,
        rsf=rsf,
        nsfr_ratio=round(nsfr_ratio, 2),
        is_compliant=nsfr_ratio >= config.NSFR_MIN_RATIO,
    )


def get_nsfr_summary(result: NSFRResult) -> dict:
    """NSFR sonuçlarının özet tablosunu döndürür."""
    # ASF kategorilere göre grupla
    asf_by_category = {}
    for item in result.asf.items_detail:
        cat = item["instrument_type"]
        if cat not in asf_by_category:
            asf_by_category[cat] = {"amount": 0, "contribution": 0}
        asf_by_category[cat]["amount"] += item["amount"]
        asf_by_category[cat]["contribution"] += item["contribution"]
    
    # RSF kategorilere göre grupla
    rsf_by_category = {}
    for item in result.rsf.items_detail:
        cat = item["instrument_type"]
        if cat not in rsf_by_category:
            rsf_by_category[cat] = {"amount": 0, "contribution": 0}
        rsf_by_category[cat]["amount"] += item["amount"]
        rsf_by_category[cat]["contribution"] += item["contribution"]
    
    return {
        "asf_total": result.asf.total_asf,
        "rsf_total": result.rsf.total_rsf,
        "nsfr_ratio": result.nsfr_ratio,
        "is_compliant": result.is_compliant,
        "asf_by_category": asf_by_category,
        "rsf_by_category": rsf_by_category,
    }
