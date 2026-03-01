# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — LCR (Likidite Karşılama Oranı) Hesaplama Motoru
Basel III / BDDK düzenlemesine uygun LCR hesaplama.
Para birimi bazlı (TL / YP) ayrı hesaplama desteği.

LCR = HQLA Stoku / Net Nakit Çıkışları (30 gün) × 100
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Optional
from models import (
    BalanceSheetItem, OffBalanceSheetItem,
    HQLABreakdown, LCRResult
)
from engines.katilim_mapping import (
    classify_hqla, get_hqla_haircut,
    get_runoff_rate, get_off_balance_runoff,
    get_inflow_rate, split_by_currency
)
import config


def calculate_hqla(assets: List[BalanceSheetItem]) -> HQLABreakdown:
    """
    HQLA (High Quality Liquid Assets) stokunu hesaplar.
    
    Level 1: Nakit, TCMB, Devlet Sukuk → %0 haircut
    Level 2A: AA- ve üstü özel sektör Sukuk → %15 haircut
    Level 2B: Diğer Sukuk → %50 haircut
    
    Cap kuralları:
    - Level 2 toplam ≤ HQLA'nın %40'ı
    - Level 2B ≤ HQLA'nın %15'i
    """
    result = HQLABreakdown()
    details = []
    
    for item in assets:
        if item.side != "aktif":
            continue
        
        hqla_level = classify_hqla(item)
        if hqla_level == "none":
            continue
        
        haircut = get_hqla_haircut(hqla_level)
        after_haircut = item.amount * (1 - haircut)
        
        detail = {
            "name": item.name,
            "amount": item.amount,
            "hqla_level": hqla_level,
            "haircut": haircut,
            "after_haircut": after_haircut,
            "currency": item.currency,
            "instrument_type": item.instrument_type,
        }
        details.append(detail)
        
        if hqla_level == "level_1":
            result.level_1 += item.amount  # Level 1 haircut yok
        elif hqla_level == "level_2a":
            result.level_2a_gross += item.amount
            result.level_2a_after_haircut += after_haircut
        elif hqla_level == "level_2b":
            result.level_2b_gross += item.amount
            result.level_2b_after_haircut += after_haircut
    
    # Cap uygulamadan önce toplam
    result.total_before_cap = (
        result.level_1 +
        result.level_2a_after_haircut +
        result.level_2b_after_haircut
    )
    
    # Cap kontrolü
    # Level 2B ≤ HQLA'nın %15'i
    max_level_2b = result.total_before_cap * config.HQLA_LEVEL2B_CAP
    if result.level_2b_after_haircut > max_level_2b:
        result.level_2b_cap_adjustment = result.level_2b_after_haircut - max_level_2b
        result.level_2b_after_haircut = max_level_2b
    
    # Level 2 (2A + 2B) ≤ HQLA'nın %40'ı
    level_2_total = result.level_2a_after_haircut + result.level_2b_after_haircut
    max_level_2 = (result.level_1 + level_2_total) * config.HQLA_LEVEL2_CAP
    if level_2_total > max_level_2:
        result.level_2_cap_adjustment = level_2_total - max_level_2
        # Önce 2B'den kes, sonra 2A'dan
        cut = result.level_2_cap_adjustment
        if result.level_2b_after_haircut >= cut:
            result.level_2b_after_haircut -= cut
        else:
            cut -= result.level_2b_after_haircut
            result.level_2b_after_haircut = 0
            result.level_2a_after_haircut -= cut
    
    result.total_hqla = (
        result.level_1 +
        result.level_2a_after_haircut +
        result.level_2b_after_haircut
    )
    result.items_detail = details
    
    return result


def calculate_outflows(
    liabilities: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
) -> tuple:
    """
    30 günlük nakit çıkışlarını hesaplar.
    
    Returns:
        (total_outflows, detail_list)
    """
    total = 0.0
    details = []
    
    # Bilanço içi çıkışlar
    for item in liabilities:
        if item.side != "pasif":
            continue
        if "ozkaynak" in item.instrument_type:
            continue
        
        runoff = get_runoff_rate(item)
        outflow = item.amount * runoff
        
        if outflow > 0:
            details.append({
                "name": item.name,
                "amount": item.amount,
                "runoff_rate": runoff,
                "outflow": outflow,
                "source": "bilanço_içi",
                "currency": item.currency,
            })
            total += outflow
    
    # Bilanço dışı çıkışlar
    if off_balance:
        for item in off_balance:
            runoff = get_off_balance_runoff(item)
            outflow = item.amount * runoff
            
            if outflow > 0:
                details.append({
                    "name": item.name,
                    "amount": item.amount,
                    "runoff_rate": runoff,
                    "outflow": outflow,
                    "source": "bilanço_dışı",
                    "currency": item.currency,
                })
                total += outflow
    
    return total, details


def calculate_inflows(assets: List[BalanceSheetItem]) -> tuple:
    """
    30 günlük nakit girişlerini hesaplar.
    
    Returns:
        (total_inflows, detail_list)
    """
    total = 0.0
    details = []
    
    for item in assets:
        if item.side != "aktif":
            continue
        
        inflow_rate = get_inflow_rate(item)
        inflow = item.amount * inflow_rate
        
        if inflow > 0:
            details.append({
                "name": item.name,
                "amount": item.amount,
                "inflow_rate": inflow_rate,
                "inflow": inflow,
                "currency": item.currency,
            })
            total += inflow
    
    return total, details


def calculate_lcr(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
    currency_filter: str = None,
) -> LCRResult:
    """
    LCR (Likidite Karşılama Oranı) hesaplar.
    
    LCR = HQLA / Net Nakit Çıkışları × 100
    Net Çıkışlar = Toplam Çıkışlar - min(Toplam Girişler, Toplam Çıkışlar × 0.75)
    
    Args:
        balance_sheet: Bilanço kalemleri
        off_balance: Bilanço dışı kalemler
        currency_filter: None=tümü, "TL"=sadece TL, "YP"=yabancı para
    """
    # Para birimi filtresi uygula
    if currency_filter:
        split = split_by_currency(balance_sheet)
        if currency_filter.upper() == "TL":
            filtered_bs = split["TL"]
        elif currency_filter.upper() == "YP":
            filtered_bs = split["YP"] + split["XAU"]
        else:
            filtered_bs = balance_sheet
        
        # Off-balance sheet da filtrele
        filtered_obs = None
        if off_balance:
            obs_split = split_by_currency(off_balance)
            if currency_filter.upper() == "TL":
                filtered_obs = obs_split["TL"]
            elif currency_filter.upper() == "YP":
                filtered_obs = obs_split["YP"] + obs_split["XAU"]
            else:
                filtered_obs = off_balance
    else:
        filtered_bs = balance_sheet
        filtered_obs = off_balance
    
    # HQLA hesapla
    aktifler = [i for i in filtered_bs if i.side == "aktif"]
    pasifler = [i for i in filtered_bs if i.side == "pasif"]
    
    hqla = calculate_hqla(aktifler)
    
    # Çıkışlar
    total_outflows, outflow_detail = calculate_outflows(pasifler, filtered_obs)
    
    # Girişler
    total_inflows, inflow_detail = calculate_inflows(aktifler)
    
    # Inflow cap: Girişler ≤ Çıkışların %75'i
    inflow_cap = total_outflows * config.INFLOW_CAP
    inflow_cap_applied = total_inflows > inflow_cap
    capped_inflows = min(total_inflows, inflow_cap)
    
    # Net çıkışlar
    net_outflows = total_outflows - capped_inflows
    
    # LCR hesapla
    if net_outflows > 0:
        lcr_ratio = (hqla.total_hqla / net_outflows) * 100
    else:
        lcr_ratio = 999.99  # Çıkış yoksa çok yüksek
    
    currency_label = currency_filter.upper() if currency_filter else "TOTAL"
    
    return LCRResult(
        hqla=hqla,
        total_outflows=total_outflows,
        total_inflows=total_inflows,
        inflow_cap_applied=inflow_cap_applied,
        net_outflows=net_outflows,
        lcr_ratio=round(lcr_ratio, 2),
        is_compliant=lcr_ratio >= config.LCR_MIN_RATIO,
        currency=currency_label,
        outflow_detail=outflow_detail,
        inflow_detail=inflow_detail,
    )


def calculate_lcr_by_currency(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
) -> dict:
    """
    Para birimi bazlı LCR hesaplar.
    BDDK toplam LCR yanında TL ve YP ayrı LCR de istiyor.
    
    Returns:
        dict: {"TOTAL": LCRResult, "TL": LCRResult, "YP": LCRResult}
    """
    return {
        "TOTAL": calculate_lcr(balance_sheet, off_balance, None),
        "TL": calculate_lcr(balance_sheet, off_balance, "TL"),
        "YP": calculate_lcr(balance_sheet, off_balance, "YP"),
    }
