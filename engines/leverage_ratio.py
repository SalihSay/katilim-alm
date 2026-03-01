# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Kaldıraç Oranı (Leverage Ratio) Motoru
Basel III'ün üçüncü sütunu. BDDK asgari %3 gerektirir.

Kaldıraç Oranı = Çekirdek Sermaye (Tier 1) / Toplam Risk Tutarı × 100
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from models import BalanceSheetItem, OffBalanceSheetItem, LeverageRatioResult
import config


def calculate_leverage_ratio(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
    tier1_capital: float = None,
) -> LeverageRatioResult:
    """
    Kaldıraç oranı hesaplar.
    
    Kaldıraç Oranı = Tier 1 Capital / Total Exposure × 100
    
    Toplam Risk Tutarı = Bilanço İçi + Bilanço Dışı (CCF uygulanmış)
    """
    result = LeverageRatioResult()
    detail = []
    
    # Tier 1 sermaye (eğer verilmediyse özkaynaklardan hesapla)
    if tier1_capital is None:
        tier1_capital = sum(
            i.amount for i in balance_sheet
            if i.side == "pasif" and "ozkaynak" in i.instrument_type
        )
    result.tier1_capital = tier1_capital
    
    # Bilanço içi risk tutarı (tüm aktifler)
    on_balance = 0.0
    for item in balance_sheet:
        if item.side == "aktif":
            on_balance += item.amount
            detail.append({
                "name": item.name,
                "amount": item.amount,
                "type": "bilanço_içi",
                "ccf": 1.0,
                "exposure": item.amount,
            })
    result.on_balance_exposure = on_balance
    
    # Bilanço dışı risk tutarı (CCF uygulanmış)
    off_exposure = 0.0
    if off_balance:
        for item in off_balance:
            ccf = item.ccf if item.ccf > 0 else config.LEVERAGE_PARAMS.get(
                f"ccf_{item.item_type}", 0.10
            )
            exposure = item.amount * ccf
            off_exposure += exposure
            detail.append({
                "name": item.name,
                "amount": item.amount,
                "type": "bilanço_dışı",
                "ccf": ccf,
                "exposure": exposure,
            })
    result.off_balance_exposure = off_exposure
    
    # Toplam risk tutarı
    result.total_exposure = on_balance + off_exposure
    
    # Kaldıraç oranı
    if result.total_exposure > 0:
        result.leverage_ratio = round(
            (tier1_capital / result.total_exposure) * 100, 2
        )
    else:
        result.leverage_ratio = 0.0
    
    result.is_compliant = result.leverage_ratio >= config.LEVERAGE_PARAMS["min_ratio"]
    result.detail = detail
    
    return result
