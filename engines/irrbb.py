# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — IRRBB (Interest Rate Risk in the Banking Book) Motoru
Katılım bankalarında "Kâr Payı Oranı Riski" olarak adlandırılır.

İki ana ölçüt:
- ΔEVE (Economic Value of Equity) — Faiz şoku altında özkaynakların ekonomik değer değişimi
- ΔNII (Net Interest Income) — Faiz şoku altında net kâr payı gelirindeki değişim
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict
import numpy as np
from models import BalanceSheetItem, IRRBBResult
from engines.duration_calc import (
    calculate_item_duration, portfolio_duration,
    duration_gap, equity_value_change
)
import config


def build_yield_curve(base_rates: dict = None) -> dict:
    """
    Kâr payı eğrisi oluşturur.
    
    Returns:
        dict: {vade_yıl: oran} — Ör: {0.25: 0.42, 0.5: 0.43, ...}
    """
    if base_rates is None:
        from engines.data_generator import generate_yield_curve
        monthly_curve = generate_yield_curve()
        # Ay → Yıl dönüşümü
        return {m / 12: r for m, r in monthly_curve.items()}
    
    return base_rates


def apply_yield_shock(
    yield_curve: dict,
    scenario: dict,
) -> dict:
    """
    Yield curve'e şok uygular.
    
    Args:
        yield_curve: {vade_yıl: oran}
        scenario: {"short": bp, "long": bp}
    """
    shocked = {}
    short_shock = scenario["short"] / 10000
    long_shock = scenario["long"] / 10000
    
    for tenor, rate in yield_curve.items():
        # Kısa vade: <1 yıl, Uzun vade: >=1 yıl
        # Ara vadeler: interpolasyon
        if tenor <= 1:
            weight = tenor  # 0-1 arası interpolasyon
            shock = short_shock * (1 - weight) + long_shock * weight
        else:
            shock = long_shock
        
        shocked[tenor] = max(0, rate + shock)  # Negatif faiz yok (katılım bankası)
    
    return shocked


def calculate_eve(
    balance_sheet: List[BalanceSheetItem],
    yield_curve: dict,
) -> float:
    """
    Economic Value of Equity (EVE) hesaplar.
    EVE = PV(Aktifler) - PV(Pasifler)
    """
    pv_assets = 0.0
    pv_liabilities = 0.0
    
    for item in balance_sheet:
        if item.amount <= 0:
            continue
        
        # Vadeye göre uygun yield bul
        tenor_years = item.maturity_days / 365
        y = _interpolate_yield(yield_curve, tenor_years)
        
        # Basit PV hesabı
        if tenor_years <= 0:
            pv = item.amount
        else:
            pv = item.amount / ((1 + y) ** tenor_years)
        
        if item.side == "aktif":
            pv_assets += pv
        elif item.side == "pasif" and "ozkaynak" not in item.instrument_type:
            pv_liabilities += pv
    
    return pv_assets - pv_liabilities


def calculate_nii(
    balance_sheet: List[BalanceSheetItem],
    yield_curve: dict,
    horizon_months: int = 12,
) -> float:
    """
    Net Interest Income (NII) / Net Kâr Payı Geliri hesaplar.
    NII = Kâr Payı Gelirleri (Aktif) - Kâr Payı Giderleri (Pasif)
    """
    interest_income = 0.0
    interest_expense = 0.0
    
    for item in balance_sheet:
        if item.amount <= 0:
            continue
        
        rate = item.profit_rate
        if rate <= 0:
            # Yield curve'den oran al
            tenor_years = item.maturity_days / 365
            rate = _interpolate_yield(yield_curve, tenor_years)
        
        # Yıllık gelir/gider × horizon/12
        annual_amount = item.amount * rate
        period_amount = annual_amount * horizon_months / 12
        
        if item.side == "aktif":
            interest_income += period_amount
        elif item.side == "pasif" and "ozkaynak" not in item.instrument_type:
            interest_expense += period_amount
    
    return interest_income - interest_expense


def run_irrbb_analysis(
    balance_sheet: List[BalanceSheetItem],
    yield_curve: dict = None,
    equity: float = None,
) -> List[IRRBBResult]:
    """
    IRRBB tam analiz — 6 Basel standart şok senaryosu.
    
    Returns:
        list[IRRBBResult]: Her senaryo için sonuç
    """
    if yield_curve is None:
        yield_curve = build_yield_curve()
    
    # Özkaynak toplamı
    if equity is None:
        equity = sum(
            i.amount for i in balance_sheet
            if i.side == "pasif" and "ozkaynak" in i.instrument_type
        )
    
    # Baz durum
    base_eve = calculate_eve(balance_sheet, yield_curve)
    base_nii = calculate_nii(balance_sheet, yield_curve)
    
    results = []
    
    for scenario_name, scenario in config.IRRBB_SCENARIOS.items():
        # Şoklu yield curve
        shocked_curve = apply_yield_shock(yield_curve, scenario)
        
        # Şok sonrası
        shocked_eve = calculate_eve(balance_sheet, shocked_curve)
        shocked_nii = calculate_nii(balance_sheet, shocked_curve)
        
        delta_eve = shocked_eve - base_eve
        delta_nii = shocked_nii - base_nii
        
        result = IRRBBResult(
            scenario_name=scenario_name,
            base_eve=round(base_eve, 2),
            shocked_eve=round(shocked_eve, 2),
            delta_eve=round(delta_eve, 2),
            delta_eve_pct=round((delta_eve / equity * 100) if equity > 0 else 0, 2),
            base_nii=round(base_nii, 2),
            shocked_nii=round(shocked_nii, 2),
            delta_nii=round(delta_nii, 2),
            delta_nii_pct=round((delta_nii / base_nii * 100) if base_nii != 0 else 0, 2),
        )
        results.append(result)
    
    return results


def _interpolate_yield(yield_curve: dict, tenor_years: float) -> float:
    """Yield curve'de verilen vade için lineer interpolasyon yapar."""
    if not yield_curve:
        return 0.40  # Varsayılan
    
    tenors = sorted(yield_curve.keys())
    
    if tenor_years <= tenors[0]:
        return yield_curve[tenors[0]]
    if tenor_years >= tenors[-1]:
        return yield_curve[tenors[-1]]
    
    # İki tenor arasında interpolasyon
    for i in range(len(tenors) - 1):
        if tenors[i] <= tenor_years <= tenors[i + 1]:
            t1, t2 = tenors[i], tenors[i + 1]
            r1, r2 = yield_curve[t1], yield_curve[t2]
            weight = (tenor_years - t1) / (t2 - t1) if t2 != t1 else 0
            return r1 + weight * (r2 - r1)
    
    return list(yield_curve.values())[-1]
