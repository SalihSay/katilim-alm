# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Gap Analizi (Yeniden Fiyatlama / Repricing Gap)
Bilanço kalemlerini BDDK standart vade aralıklarına göre gruplandırır.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from models import BalanceSheetItem, GapBucket
import config


def assign_bucket(maturity_days: int) -> str:
    """Bir kalemi vade aralığına (bucket) atar."""
    for bucket in config.GAP_BUCKETS:
        if bucket["min_days"] <= maturity_days <= bucket["max_days"]:
            return bucket["name"]
    return "5+ Yıl"


def build_gap_table(
    balance_sheet: List[BalanceSheetItem],
) -> List[GapBucket]:
    """
    Repricing Gap tablosu oluşturur.
    
    Her vade aralığı için:
    - Rate Sensitive Assets (RSA)
    - Rate Sensitive Liabilities (RSL)
    - Gap = RSA - RSL
    - Kümülatif Gap
    - Gap / Toplam Aktifler (%)
    """
    total_assets = sum(i.amount for i in balance_sheet if i.side == "aktif")
    
    # Bucket'ları başlat
    buckets = {}
    for b in config.GAP_BUCKETS:
        buckets[b["name"]] = GapBucket(
            bucket_name=b["name"],
            min_days=b["min_days"],
            max_days=b["max_days"],
        )
    
    # Kalemleri bucket'lara ata
    for item in balance_sheet:
        # Yeniden fiyatlama vadesi kullan (yoksa vade)
        reprice_days = item.repricing_days if item.repricing_days > 0 else item.maturity_days
        bucket_name = assign_bucket(reprice_days)
        
        if bucket_name not in buckets:
            continue
        
        if item.side == "aktif":
            buckets[bucket_name].rate_sensitive_assets += item.amount
        elif item.side == "pasif":
            # Özkaynaklar fiyatlama duyarsız
            if "ozkaynak" not in item.instrument_type:
                buckets[bucket_name].rate_sensitive_liabilities += item.amount
    
    # Gap ve kümülatif gap hesapla
    result = []
    cumulative = 0.0
    
    for b in config.GAP_BUCKETS:
        bucket = buckets[b["name"]]
        bucket.gap = bucket.rate_sensitive_assets - bucket.rate_sensitive_liabilities
        cumulative += bucket.gap
        bucket.cumulative_gap = cumulative
        bucket.gap_to_total_assets = (
            (bucket.gap / total_assets * 100) if total_assets > 0 else 0.0
        )
        result.append(bucket)
    
    return result


def calculate_nii_impact(
    gap_table: List[GapBucket],
    rate_change_bp: int = 100,
) -> float:
    """
    NII (Net Interest Income / Net Kâr Payı Geliri) etkisini hesaplar.
    
    NII Etkisi = Σ (Gap × Δr × vade_ağırlığı)
    
    Args:
        gap_table: Gap tablosu
        rate_change_bp: Kâr payı oranı değişimi (baz puan)
    
    Returns:
        float: NII değişimi (TL)
    """
    delta_r = rate_change_bp / 10000  # bp → ondalık
    total_impact = 0.0
    
    for bucket in gap_table:
        # Vade ortası (ay cinsinden) / 12 = yıl ağırlığı
        mid_days = (bucket.min_days + min(bucket.max_days, 3650)) / 2
        time_weight = mid_days / 365
        
        impact = bucket.gap * delta_r * time_weight
        total_impact += impact
    
    return total_impact


def get_gap_summary(gap_table: List[GapBucket]) -> dict:
    """Gap analizi özet bilgileri."""
    total_rsa = sum(b.rate_sensitive_assets for b in gap_table)
    total_rsl = sum(b.rate_sensitive_liabilities for b in gap_table)
    total_gap = total_rsa - total_rsl
    
    # En büyük negatif gap bucket
    worst_bucket = min(gap_table, key=lambda b: b.gap) if gap_table else None
    # En büyük pozitif gap bucket
    best_bucket = max(gap_table, key=lambda b: b.gap) if gap_table else None
    
    return {
        "total_rsa": total_rsa,
        "total_rsl": total_rsl,
        "total_gap": total_gap,
        "worst_bucket": worst_bucket.bucket_name if worst_bucket else "",
        "worst_gap": worst_bucket.gap if worst_bucket else 0,
        "best_bucket": best_bucket.bucket_name if best_bucket else "",
        "best_gap": best_bucket.gap if best_bucket else 0,
        "nii_100bp_up": calculate_nii_impact(gap_table, 100),
        "nii_100bp_down": calculate_nii_impact(gap_table, -100),
    }
