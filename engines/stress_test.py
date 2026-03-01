# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Stres Testi Motoru
FX şoku, kâr payı şoku, mevduat kaçışı, kredi kaybı uygulayarak
tüm oranları (LCR, NSFR, Kaldıraç, Duration Gap) yeniden hesaplar.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import copy
from typing import List, Dict
from models import BalanceSheetItem, OffBalanceSheetItem, StressScenario, StressResult
from engines.lcr_engine import calculate_lcr
from engines.nsfr_engine import calculate_nsfr
from engines.leverage_ratio import calculate_leverage_ratio
from engines.duration_calc import portfolio_duration, duration_gap
import config


def apply_fx_shock(
    balance_sheet: List[BalanceSheetItem],
    shock_pct: float,
) -> List[BalanceSheetItem]:
    """
    FX şoku uygular. TL değer kaybederse YP cinsinden kalemler TL karşılığı artar.
    
    Args:
        shock_pct: TL değer kaybı oranı (ör: 0.20 = %20)
    """
    result = []
    for item in balance_sheet:
        new_item = copy.deepcopy(item)
        if item.currency.upper() not in ["TL", "TRY"]:
            # YP kalem → TL karşılığı artar
            new_item.amount = item.amount * (1 + shock_pct)
        result.append(new_item)
    return result


def apply_rate_shock(
    balance_sheet: List[BalanceSheetItem],
    shock_bp: int,
) -> List[BalanceSheetItem]:
    """
    Kâr payı oranı şoku uygular.
    Aktif ve pasif taraftaki fiyatlama oranlarını değiştirir.
    """
    result = []
    delta = shock_bp / 10000
    for item in balance_sheet:
        new_item = copy.deepcopy(item)
        if new_item.profit_rate > 0:
            new_item.profit_rate = max(0.01, new_item.profit_rate + delta)
        result.append(new_item)
    return result


def apply_deposit_runoff(
    balance_sheet: List[BalanceSheetItem],
    runoff_pct: float,
) -> List[BalanceSheetItem]:
    """
    Mevduat kaçışı uygular. Katılma hesaplarından fon çıkışı simüle eder.
    
    Args:
        runoff_pct: Ekstra kaçış oranı (ör: 0.10 = %10)
    """
    result = []
    for item in balance_sheet:
        new_item = copy.deepcopy(item)
        if item.side == "pasif" and "katilma" in item.instrument_type:
            new_item.amount = item.amount * (1 - runoff_pct)
        result.append(new_item)
    return result


def apply_credit_loss(
    balance_sheet: List[BalanceSheetItem],
    loss_pct: float,
) -> List[BalanceSheetItem]:
    """
    Kredi değer kaybı uygular. Murabaha ve İcara alacaklarına zarar yazar.
    
    Args:
        loss_pct: Kredi kayıp oranı (ör: 0.05 = %5)
    """
    result = []
    for item in balance_sheet:
        new_item = copy.deepcopy(item)
        if item.side == "aktif" and item.instrument_type in [
            "murabaha_alacak", "finansal_kiralama"
        ]:
            new_item.amount = item.amount * (1 - loss_pct)
        result.append(new_item)
    return result


def run_stress_scenario(
    balance_sheet: List[BalanceSheetItem],
    scenario: StressScenario,
    off_balance: List[OffBalanceSheetItem] = None,
    base_lcr: float = None,
    base_nsfr: float = None,
    base_leverage: float = None,
    base_duration_gap: float = None,
) -> StressResult:
    """
    Stres senaryosu çalıştırır.
    Tüm şokları sırayla uygular → Tüm oranları yeniden hesaplar.
    """
    # Baz durum metrikleri
    if base_lcr is None:
        base_lcr_result = calculate_lcr(balance_sheet, off_balance)
        base_lcr = base_lcr_result.lcr_ratio
    if base_nsfr is None:
        base_nsfr_result = calculate_nsfr(balance_sheet, off_balance)
        base_nsfr = base_nsfr_result.nsfr_ratio
    if base_leverage is None:
        base_lev_result = calculate_leverage_ratio(balance_sheet, off_balance)
        base_leverage = base_lev_result.leverage_ratio
    if base_duration_gap is None:
        total_aktif = sum(i.amount for i in balance_sheet if i.side == "aktif")
        total_pasif = sum(i.amount for i in balance_sheet if i.side == "pasif")
        a_dur = portfolio_duration(balance_sheet, "aktif")
        p_dur = portfolio_duration(balance_sheet, "pasif")
        base_duration_gap = duration_gap(a_dur, p_dur, total_aktif, total_pasif)
    
    # Şokları sırayla uygula
    stressed = balance_sheet
    
    if scenario.fx_shock > 0:
        stressed = apply_fx_shock(stressed, scenario.fx_shock)
    
    if scenario.rate_shock_bp != 0:
        stressed = apply_rate_shock(stressed, scenario.rate_shock_bp)
    
    if scenario.deposit_runoff > 0:
        stressed = apply_deposit_runoff(stressed, scenario.deposit_runoff)
    
    if scenario.credit_loss > 0:
        stressed = apply_credit_loss(stressed, scenario.credit_loss)
    
    # Stres sonrası oranları hesapla
    s_lcr = calculate_lcr(stressed, off_balance)
    s_nsfr = calculate_nsfr(stressed, off_balance)
    s_lev = calculate_leverage_ratio(stressed, off_balance)
    
    s_total_aktif = sum(i.amount for i in stressed if i.side == "aktif")
    s_total_pasif = sum(i.amount for i in stressed if i.side == "pasif")
    s_a_dur = portfolio_duration(stressed, "aktif")
    s_p_dur = portfolio_duration(stressed, "pasif")
    s_dur_gap = duration_gap(s_a_dur, s_p_dur, s_total_aktif, s_total_pasif)
    
    return StressResult(
        scenario=scenario,
        base_lcr=base_lcr,
        stressed_lcr=s_lcr.lcr_ratio,
        base_nsfr=base_nsfr,
        stressed_nsfr=s_nsfr.nsfr_ratio,
        base_leverage=base_leverage,
        stressed_leverage=s_lev.leverage_ratio,
        base_duration_gap=base_duration_gap,
        stressed_duration_gap=s_dur_gap,
        lcr_impact=round(s_lcr.lcr_ratio - base_lcr, 2),
        nsfr_impact=round(s_nsfr.nsfr_ratio - base_nsfr, 2),
        lcr_compliant=s_lcr.is_compliant,
        nsfr_compliant=s_nsfr.is_compliant,
        leverage_compliant=s_lev.is_compliant,
    )


def compare_scenarios(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
    scenarios: List[StressScenario] = None,
) -> List[StressResult]:
    """
    Birden fazla senaryoyu karşılaştırır.
    """
    if scenarios is None:
        scenarios = load_preset_scenarios()
    
    # Baz durum bir kez hesapla
    base_lcr = calculate_lcr(balance_sheet, off_balance).lcr_ratio
    base_nsfr = calculate_nsfr(balance_sheet, off_balance).nsfr_ratio
    base_lev = calculate_leverage_ratio(balance_sheet, off_balance).leverage_ratio
    
    total_aktif = sum(i.amount for i in balance_sheet if i.side == "aktif")
    total_pasif = sum(i.amount for i in balance_sheet if i.side == "pasif")
    a_dur = portfolio_duration(balance_sheet, "aktif")
    p_dur = portfolio_duration(balance_sheet, "pasif")
    base_dur_gap = duration_gap(a_dur, p_dur, total_aktif, total_pasif)
    
    results = []
    for scenario in scenarios:
        result = run_stress_scenario(
            balance_sheet, scenario, off_balance,
            base_lcr, base_nsfr, base_lev, base_dur_gap,
        )
        results.append(result)
    
    return results


def sensitivity_analysis(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
) -> Dict:
    """
    Her risk faktörünün LCR üzerindeki bireysel etkisi (tornado chart için).
    """
    base_lcr = calculate_lcr(balance_sheet, off_balance).lcr_ratio
    
    factors = {
        "FX %10 Şoku": StressScenario(name="FX", fx_shock=0.10),
        "FX %20 Şoku": StressScenario(name="FX", fx_shock=0.20),
        "Kâr Payı +200bp": StressScenario(name="Rate", rate_shock_bp=200),
        "Kâr Payı +400bp": StressScenario(name="Rate", rate_shock_bp=400),
        "Mevduat Kaçışı %5": StressScenario(name="Deposit", deposit_runoff=0.05),
        "Mevduat Kaçışı %10": StressScenario(name="Deposit", deposit_runoff=0.10),
        "Kredi Kaybı %2": StressScenario(name="Credit", credit_loss=0.02),
        "Kredi Kaybı %5": StressScenario(name="Credit", credit_loss=0.05),
    }
    
    results = {}
    for name, scenario in factors.items():
        result = run_stress_scenario(
            balance_sheet, scenario, off_balance,
            base_lcr=base_lcr,
        )
        results[name] = {
            "base_lcr": base_lcr,
            "stressed_lcr": result.stressed_lcr,
            "impact": result.lcr_impact,
        }
    
    return results


def load_preset_scenarios() -> List[StressScenario]:
    """Önceden tanımlı stres senaryolarını yükler."""
    scenarios = []
    for name, params in config.STRESS_SCENARIOS.items():
        scenarios.append(StressScenario(
            name=name,
            fx_shock=params["fx_shock"],
            rate_shock_bp=params["rate_shock_bp"],
            deposit_runoff=params["deposit_runoff"],
            credit_loss=params["credit_loss"],
            description=params.get("description", ""),
        ))
    return scenarios
