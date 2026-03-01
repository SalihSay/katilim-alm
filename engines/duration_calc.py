# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Duration & Convexity Hesaplama Motoru
Macaulay Duration, Modified Duration, Convexity ve Duration Gap hesaplama.
Katılım bankası notu: "Yield" yerine "kâr payı oranı (profit rate)" kullanılır.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from typing import List
from models import BalanceSheetItem, DurationResult


def macaulay_duration(
    cashflows: List[float],
    yield_rate: float,
    freq: int = 2,
) -> float:
    """
    Macaulay Duration hesaplar.
    
    Duration = Σ [t × CFₜ / (1+y/n)^(t)] / Σ [CFₜ / (1+y/n)^(t)]
    
    Args:
        cashflows: Dönemsel nakit akışları [CF₁, CF₂, ...]
        yield_rate: Yıllık kâr payı oranı (ondalık)
        freq: Yıllık kupon/ödeme sıklığı (1=yıllık, 2=6 aylık, 4=çeyreklik, 12=aylık)
    """
    if not cashflows or yield_rate < 0:
        return 0.0
    
    y = yield_rate / freq
    pv_weighted = 0.0
    pv_total = 0.0
    
    for t, cf in enumerate(cashflows, 1):
        discount = (1 + y) ** t
        pv = cf / discount
        pv_weighted += (t / freq) * pv
        pv_total += pv
    
    if pv_total == 0:
        return 0.0
    
    return pv_weighted / pv_total


def modified_duration(mac_duration: float, yield_rate: float, freq: int = 2) -> float:
    """
    Modified Duration hesaplar.
    
    Modified Duration = Macaulay Duration / (1 + y/n)
    """
    y = yield_rate / freq
    if (1 + y) == 0:
        return 0.0
    return mac_duration / (1 + y)


def convexity(
    cashflows: List[float],
    yield_rate: float,
    freq: int = 2,
) -> float:
    """
    Convexity hesaplar.
    
    Convexity = Σ [t(t+1) × CFₜ / (1+y/n)^(t+2)] / P
    """
    if not cashflows or yield_rate < 0:
        return 0.0
    
    y = yield_rate / freq
    conv_sum = 0.0
    pv_total = 0.0
    
    for t, cf in enumerate(cashflows, 1):
        discount = (1 + y) ** t
        pv = cf / discount
        pv_total += pv
        conv_sum += t * (t + 1) * cf / ((1 + y) ** (t + 2))
    
    if pv_total == 0:
        return 0.0
    
    return conv_sum / (pv_total * freq * freq)


def price_change_estimate(
    mod_dur: float,
    conv: float,
    delta_yield: float,
) -> float:
    """
    Fiyat değişikliği tahmini (2. derece Taylor yaklaşımı).
    
    ΔP/P ≈ -ModDuration × Δy + ½ × Convexity × (Δy)²
    
    Args:
        mod_dur: Modified Duration
        conv: Convexity
        delta_yield: Verim değişimi (ondalık, ör: 0.01 = 100bp)
    """
    return -mod_dur * delta_yield + 0.5 * conv * delta_yield ** 2


def generate_bond_cashflows(
    face_value: float,
    coupon_rate: float,
    periods: int,
    freq: int = 2,
) -> List[float]:
    """
    Sukuk/Tahvil nakit akışlarını üretir.
    
    Args:
        face_value: Nominal (yüz) değer
        coupon_rate: Yıllık kupon/kâr payı oranı
        periods: Toplam dönem sayısı
        freq: Yıllık ödeme sıklığı
    """
    if periods <= 0:
        return [face_value]
    
    periodic_coupon = face_value * coupon_rate / freq
    cashflows = [periodic_coupon] * (periods - 1)
    cashflows.append(periodic_coupon + face_value)  # Son dönem anapara + kupon
    return cashflows


def calculate_item_duration(item: BalanceSheetItem) -> DurationResult:
    """
    Tek bir bilanço kalemi için duration hesaplar.
    """
    if item.maturity_days <= 0 or item.amount <= 0:
        return DurationResult(item_name=item.name)
    
    # Vadeyi yıla çevir
    years = item.maturity_days / 365
    
    # Kâr payı oranı yoksa sıfır kupon — duration = vade
    if item.profit_rate <= 0:
        return DurationResult(
            macaulay_duration=years,
            modified_duration=years,
            convexity=years * (years + 1 / 365),
            item_name=item.name,
        )
    
    # Kupon dönem sayısı (6 aylık varsayım)
    freq = 2
    periods = max(1, int(years * freq))
    
    # Nakit akışları üret
    cfs = generate_bond_cashflows(item.amount, item.profit_rate, periods, freq)
    
    # Duration hesapla
    mac_dur = macaulay_duration(cfs, item.profit_rate, freq)
    mod_dur = modified_duration(mac_dur, item.profit_rate, freq)
    conv = convexity(cfs, item.profit_rate, freq)
    
    return DurationResult(
        macaulay_duration=round(mac_dur, 4),
        modified_duration=round(mod_dur, 4),
        convexity=round(conv, 4),
        item_name=item.name,
    )


def portfolio_duration(
    items: List[BalanceSheetItem],
    side: str = "aktif",
) -> float:
    """
    Portföy ağırlıklı ortalama duration hesaplar.
    
    Portfolio Duration = Σ (wᵢ × Dᵢ)
    wᵢ = Kalem tutarı / Toplam tutar
    """
    filtered = [i for i in items if i.side == side and i.amount > 0]
    total = sum(i.amount for i in filtered)
    
    if total == 0:
        return 0.0
    
    weighted_sum = 0.0
    for item in filtered:
        dur = calculate_item_duration(item)
        weight = item.amount / total
        weighted_sum += weight * dur.modified_duration
    
    return round(weighted_sum, 4)


def duration_gap(
    asset_duration: float,
    liability_duration: float,
    total_assets: float,
    total_liabilities: float,
) -> float:
    """
    Duration Gap hesaplar.
    
    Duration Gap = D_A - (L/A) × D_L
    
    Pozitif gap → faiz artışında özkaynak değer kaybeder
    Negatif gap → faiz düşüşünde özkaynak değer kaybeder
    """
    if total_assets == 0:
        return 0.0
    
    leverage = total_liabilities / total_assets
    return round(asset_duration - leverage * liability_duration, 4)


def equity_value_change(
    dur_gap: float,
    total_assets: float,
    delta_yield: float,
) -> float:
    """
    Duration Gap'e dayalı özkaynak değer değişimi.
    
    ΔE ≈ -Duration Gap × A × Δy / (1 + y)
    
    Basitleştirilmiş: ΔE ≈ -Duration Gap × A × Δy
    """
    return -dur_gap * total_assets * delta_yield
