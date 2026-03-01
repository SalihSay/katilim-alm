# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Sentetik Veri Üretici
BDDK sektör raporlarındaki oranlara yakın gerçekçi katılım bankası bilanço verisi üretir.
"""
import random
import math
from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
import numpy as np

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import (
    BalanceSheetItem, CashFlow, OffBalanceSheetItem,
    ProfitPool, StressScenario
)
import config


def generate_balance_sheet(
    seed: int = 42,
    total_assets_tl: float = 50_000_000_000,  # 50 Milyar TL
    report_date: date = None,
) -> List[BalanceSheetItem]:
    """
    Gerçekçi katılım bankası bilanço verisi üretir.
    BDDK sektör raporlarındaki katılım bankası bilanço dağılımına yakın.
    
    Args:
        seed: Random seed (tekrarlanabilirlik)
        total_assets_tl: Toplam aktif büyüklüğü (TL)
        report_date: Rapor tarihi
        
    Returns:
        list[BalanceSheetItem]: Bilanço kalemleri
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)
    
    if report_date is None:
        report_date = date.today()
    
    items = []
    T = total_assets_tl
    
    # ==========================================
    # AKTİF KALEMLER
    # ==========================================
    
    # 1. Nakit & Merkez Bankası (%8-12)
    nakit_ratio = rng.uniform(0.08, 0.12)
    nakit_tl = T * nakit_ratio * 0.4
    items.append(BalanceSheetItem(
        name="Nakit ve Kasa Mevcudu",
        amount=nakit_tl,
        currency="TL",
        amount_original=nakit_tl,
        side="aktif",
        instrument_type="nakit",
        islamic_class="Nakit",
        maturity_days=0,
        profit_rate=0.0,
        counterparty_type="",
        hqla_level="level_1",
    ))
    
    tcmb_tl = T * nakit_ratio * 0.35
    items.append(BalanceSheetItem(
        name="TCMB Zorunlu Karşılıklar (TL)",
        amount=tcmb_tl,
        currency="TL",
        amount_original=tcmb_tl,
        side="aktif",
        instrument_type="merkez_bankasi",
        islamic_class="Merkez Bankası",
        maturity_days=0,
        profit_rate=0.0,
        counterparty_type="devlet",
        hqla_level="level_1",
    ))
    
    tcmb_usd = T * nakit_ratio * 0.25
    items.append(BalanceSheetItem(
        name="TCMB Zorunlu Karşılıklar (USD)",
        amount=tcmb_usd,
        currency="USD",
        amount_original=tcmb_usd / config.DEFAULT_FX_RATES["USD_TL"],
        side="aktif",
        instrument_type="merkez_bankasi",
        islamic_class="Merkez Bankası",
        maturity_days=0,
        profit_rate=0.0,
        counterparty_type="devlet",
        hqla_level="level_1",
    ))
    
    # 2. Murabaha Alacakları (%45-55 — katılım bankaları için en büyük kalem)
    murabaha_ratio = rng.uniform(0.45, 0.55)
    
    # Kısa vade Murabaha TL
    mur_kisa_tl = T * murabaha_ratio * 0.20
    items.append(BalanceSheetItem(
        name="Murabaha Alacakları (Kısa Vade, TL)",
        amount=mur_kisa_tl,
        currency="TL",
        amount_original=mur_kisa_tl,
        side="aktif",
        instrument_type="murabaha_alacak",
        islamic_class="Murabaha",
        maturity_days=rng.randint(30, 180),
        repricing_days=rng.randint(30, 90),
        profit_rate=round(rng.uniform(0.40, 0.55), 4),
        counterparty_type="kurumsal",
    ))
    
    # Uzun vade Murabaha TL
    mur_uzun_tl = T * murabaha_ratio * 0.35
    items.append(BalanceSheetItem(
        name="Murabaha Alacakları (Uzun Vade, TL)",
        amount=mur_uzun_tl,
        currency="TL",
        amount_original=mur_uzun_tl,
        side="aktif",
        instrument_type="murabaha_alacak",
        islamic_class="Murabaha",
        maturity_days=rng.randint(365, 1825),
        repricing_days=rng.randint(90, 365),
        profit_rate=round(rng.uniform(0.35, 0.50), 4),
        counterparty_type="kurumsal",
    ))
    
    # Murabaha USD
    mur_usd = T * murabaha_ratio * 0.15
    items.append(BalanceSheetItem(
        name="Murabaha Alacakları (USD)",
        amount=mur_usd,
        currency="USD",
        amount_original=mur_usd / config.DEFAULT_FX_RATES["USD_TL"],
        side="aktif",
        instrument_type="murabaha_alacak",
        islamic_class="Murabaha",
        maturity_days=rng.randint(90, 730),
        repricing_days=rng.randint(90, 180),
        profit_rate=round(rng.uniform(0.05, 0.09), 4),
        counterparty_type="kurumsal",
    ))
    
    # Perakende Murabaha (Konut, Taşıt)
    mur_perakende = T * murabaha_ratio * 0.30
    items.append(BalanceSheetItem(
        name="Murabaha Alacakları (Perakende - Konut/Taşıt)",
        amount=mur_perakende,
        currency="TL",
        amount_original=mur_perakende,
        side="aktif",
        instrument_type="murabaha_alacak",
        islamic_class="Murabaha",
        maturity_days=rng.randint(730, 3650),
        repricing_days=rng.randint(180, 365),
        profit_rate=round(rng.uniform(0.30, 0.45), 4),
        counterparty_type="perakende",
    ))
    
    # 3. Finansal Kiralama / İcara (%8-12)
    icara_ratio = rng.uniform(0.08, 0.12)
    icara = T * icara_ratio
    items.append(BalanceSheetItem(
        name="Finansal Kiralama (İcara) Alacakları",
        amount=icara,
        currency="TL",
        amount_original=icara,
        side="aktif",
        instrument_type="finansal_kiralama",
        islamic_class="İcara",
        maturity_days=rng.randint(365, 2555),
        repricing_days=rng.randint(180, 365),
        profit_rate=round(rng.uniform(0.30, 0.45), 4),
        counterparty_type="kurumsal",
    ))
    
    # 4. Sukuk Portföyü (%10-15)
    sukuk_ratio = rng.uniform(0.10, 0.15)
    
    # Devlet Sukuk TL
    devlet_sukuk_tl = T * sukuk_ratio * 0.50
    items.append(BalanceSheetItem(
        name="Devlet Sukuk / Kira Sertifikası (TL)",
        amount=devlet_sukuk_tl,
        currency="TL",
        amount_original=devlet_sukuk_tl,
        side="aktif",
        instrument_type="devlet_sukuk",
        islamic_class="Sukuk",
        maturity_days=rng.randint(180, 1825),
        profit_rate=round(rng.uniform(0.25, 0.40), 4),
        counterparty_type="devlet",
        credit_rating="BB",
        hqla_level="level_1",
    ))
    
    # Devlet Sukuk USD
    devlet_sukuk_usd = T * sukuk_ratio * 0.20
    items.append(BalanceSheetItem(
        name="Devlet Sukuk / Kira Sertifikası (USD)",
        amount=devlet_sukuk_usd,
        currency="USD",
        amount_original=devlet_sukuk_usd / config.DEFAULT_FX_RATES["USD_TL"],
        side="aktif",
        instrument_type="devlet_sukuk",
        islamic_class="Sukuk",
        maturity_days=rng.randint(365, 3650),
        profit_rate=round(rng.uniform(0.06, 0.10), 4),
        counterparty_type="devlet",
        credit_rating="BB",
        hqla_level="level_1",
    ))
    
    # Özel Sektör Sukuk (Yüksek Derece)
    ozel_sukuk_aa = T * sukuk_ratio * 0.15
    items.append(BalanceSheetItem(
        name="Özel Sektör Sukuk (AA Derece)",
        amount=ozel_sukuk_aa,
        currency="TL",
        amount_original=ozel_sukuk_aa,
        side="aktif",
        instrument_type="ozel_sukuk_aa",
        islamic_class="Sukuk",
        maturity_days=rng.randint(180, 730),
        profit_rate=round(rng.uniform(0.35, 0.50), 4),
        counterparty_type="kurumsal",
        credit_rating="AA-",
        hqla_level="level_2a",
    ))
    
    # Özel Sektör Sukuk (Diğer)
    ozel_sukuk_diger = T * sukuk_ratio * 0.15
    items.append(BalanceSheetItem(
        name="Özel Sektör Sukuk (Diğer)",
        amount=ozel_sukuk_diger,
        currency="TL",
        amount_original=ozel_sukuk_diger,
        side="aktif",
        instrument_type="ozel_sukuk_diger",
        islamic_class="Sukuk",
        maturity_days=rng.randint(180, 730),
        profit_rate=round(rng.uniform(0.40, 0.55), 4),
        counterparty_type="kurumsal",
        credit_rating="BBB",
        hqla_level="level_2b",
    ))
    
    # 5. Bankalararası Murabaha Plasmanlar (%3-5)
    bankalar_plasm_ratio = rng.uniform(0.03, 0.05)
    bankalar_plasm = T * bankalar_plasm_ratio
    items.append(BalanceSheetItem(
        name="Bankalararası Murabaha Plasmanlar",
        amount=bankalar_plasm,
        currency="TL",
        amount_original=bankalar_plasm,
        side="aktif",
        instrument_type="bankalararasi_murabaha",
        islamic_class="Murabaha",
        maturity_days=rng.randint(7, 90),
        profit_rate=round(rng.uniform(0.40, 0.50), 4),
        counterparty_type="finansal",
    ))
    
    # 6. Sabit Varlıklar (%2-4)
    sabit_ratio = rng.uniform(0.02, 0.04)
    sabit = T * sabit_ratio
    items.append(BalanceSheetItem(
        name="Sabit Varlıklar (Gayrimenkul, Ekipman)",
        amount=sabit,
        currency="TL",
        amount_original=sabit,
        side="aktif",
        instrument_type="sabit_varlik",
        islamic_class="Sabit Varlık",
        maturity_days=99999,
        profit_rate=0.0,
    ))
    
    # Toplam aktif hesapla
    toplam_aktif = sum(i.amount for i in items if i.side == "aktif")
    
    # 7. Diğer Aktifler (dengeleme kalemi)
    diger_aktif = T - toplam_aktif
    if diger_aktif > 0:
        items.append(BalanceSheetItem(
            name="Diğer Aktifler",
            amount=diger_aktif,
            currency="TL",
            amount_original=diger_aktif,
            side="aktif",
            instrument_type="diger_aktif",
            islamic_class="Diğer",
            maturity_days=rng.randint(30, 365),
        ))
    
    # ==========================================
    # PASİF KALEMLER
    # ==========================================
    
    # Özkaynak oranı (%8-12)
    ozkaynak_ratio = rng.uniform(0.08, 0.12)
    ozkaynak = T * ozkaynak_ratio
    items.append(BalanceSheetItem(
        name="Özkaynaklar",
        amount=ozkaynak,
        currency="TL",
        amount_original=ozkaynak,
        side="pasif",
        instrument_type="ozkaynaklar",
        islamic_class="Özkaynak",
        maturity_days=99999,
    ))
    
    pasif_hedef = T - ozkaynak
    
    # 1. Katılma Hesapları — Vadesiz (%10-15 toplam pasifin)
    vadesiz_ratio = rng.uniform(0.10, 0.15)
    
    vadesiz_tl = pasif_hedef * vadesiz_ratio * 0.7
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadesiz, TL)",
        amount=vadesiz_tl,
        currency="TL",
        amount_original=vadesiz_tl,
        side="pasif",
        instrument_type="katilma_vadesiz",
        islamic_class="Katılma Hesabı",
        maturity_days=0,
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    vadesiz_usd = pasif_hedef * vadesiz_ratio * 0.3
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadesiz, USD)",
        amount=vadesiz_usd,
        currency="USD",
        amount_original=vadesiz_usd / config.DEFAULT_FX_RATES["USD_TL"],
        side="pasif",
        instrument_type="katilma_vadesiz",
        islamic_class="Katılma Hesabı",
        maturity_days=0,
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 2. Katılma Hesapları — Vadeli (%45-55)
    vadeli_ratio = rng.uniform(0.45, 0.55)
    
    # 1-3 Ay Vadeli TL
    v_1_3 = pasif_hedef * vadeli_ratio * 0.30
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadeli 1-3 Ay, TL)",
        amount=v_1_3,
        currency="TL",
        amount_original=v_1_3,
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(30, 90),
        profit_rate=round(rng.uniform(0.35, 0.50), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 3-6 Ay Vadeli TL
    v_3_6 = pasif_hedef * vadeli_ratio * 0.25
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadeli 3-6 Ay, TL)",
        amount=v_3_6,
        currency="TL",
        amount_original=v_3_6,
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(91, 180),
        profit_rate=round(rng.uniform(0.38, 0.52), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 6-12 Ay Vadeli TL
    v_6_12 = pasif_hedef * vadeli_ratio * 0.20
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadeli 6-12 Ay, TL)",
        amount=v_6_12,
        currency="TL",
        amount_original=v_6_12,
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(181, 365),
        profit_rate=round(rng.uniform(0.40, 0.55), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 1 Yıl+ Vadeli TL
    v_1y = pasif_hedef * vadeli_ratio * 0.10
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadeli 1 Yıl+, TL)",
        amount=v_1y,
        currency="TL",
        amount_original=v_1y,
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(366, 730),
        profit_rate=round(rng.uniform(0.42, 0.55), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # Vadeli USD
    v_usd = pasif_hedef * vadeli_ratio * 0.15
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Vadeli, USD)",
        amount=v_usd,
        currency="USD",
        amount_original=v_usd / config.DEFAULT_FX_RATES["USD_TL"],
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(30, 365),
        profit_rate=round(rng.uniform(0.03, 0.06), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 3. Altın Katılma Hesabı (%3-5)
    altin_ratio = rng.uniform(0.03, 0.05)
    altin = pasif_hedef * altin_ratio
    items.append(BalanceSheetItem(
        name="Katılma Hesabı (Altın - XAU)",
        amount=altin,
        currency="XAU",
        amount_original=altin / config.DEFAULT_FX_RATES["XAU_TL"],
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(30, 180),
        profit_rate=round(rng.uniform(0.01, 0.03), 4),
        is_insured=True,
        counterparty_type="perakende",
    ))
    
    # 4. İhraç Edilen Sukuk (%5-8)
    ihrac_ratio = rng.uniform(0.05, 0.08)
    ihrac = pasif_hedef * ihrac_ratio
    items.append(BalanceSheetItem(
        name="İhraç Edilen Sukuk (Kira Sertifikası)",
        amount=ihrac,
        currency="TL",
        amount_original=ihrac,
        side="pasif",
        instrument_type="ihrac_sukuk",
        islamic_class="Sukuk İhracı",
        maturity_days=rng.randint(365, 1825),
        profit_rate=round(rng.uniform(0.35, 0.48), 4),
        counterparty_type="kurumsal",
    ))
    
    # 5. Bankalararası Murabaha Borçları (%8-12)
    bankalar_borc_ratio = rng.uniform(0.08, 0.12)
    
    bankalar_kisa = pasif_hedef * bankalar_borc_ratio * 0.6
    items.append(BalanceSheetItem(
        name="Bankalararası Murabaha Borçları (Kısa Vade)",
        amount=bankalar_kisa,
        currency="TL",
        amount_original=bankalar_kisa,
        side="pasif",
        instrument_type="bankalararasi_borc",
        islamic_class="Bankalararası Murabaha",
        maturity_days=rng.randint(7, 90),
        profit_rate=round(rng.uniform(0.42, 0.50), 4),
        counterparty_type="finansal",
    ))
    
    bankalar_uzun = pasif_hedef * bankalar_borc_ratio * 0.4
    items.append(BalanceSheetItem(
        name="Bankalararası Murabaha Borçları (Uzun Vade, USD)",
        amount=bankalar_uzun,
        currency="USD",
        amount_original=bankalar_uzun / config.DEFAULT_FX_RATES["USD_TL"],
        side="pasif",
        instrument_type="bankalararasi_borc",
        islamic_class="Bankalararası Murabaha",
        maturity_days=rng.randint(180, 730),
        profit_rate=round(rng.uniform(0.05, 0.08), 4),
        counterparty_type="finansal",
    ))
    
    # 6. Kurumsal Katılma Hesapları (%5-8)
    kurumsal_ratio = rng.uniform(0.05, 0.08)
    kurumsal = pasif_hedef * kurumsal_ratio
    items.append(BalanceSheetItem(
        name="Kurumsal Katılma Hesapları",
        amount=kurumsal,
        currency="TL",
        amount_original=kurumsal,
        side="pasif",
        instrument_type="katilma_vadeli",
        islamic_class="Katılma Hesabı",
        maturity_days=rng.randint(30, 365),
        profit_rate=round(rng.uniform(0.40, 0.52), 4),
        is_insured=False,
        counterparty_type="kurumsal",
    ))
    
    # Dengeleme: Diğer Yükümlülükler
    toplam_pasif = sum(i.amount for i in items if i.side == "pasif")
    diger_pasif = T - toplam_pasif
    if diger_pasif > 0:
        items.append(BalanceSheetItem(
            name="Diğer Yükümlülükler",
            amount=diger_pasif,
            currency="TL",
            amount_original=diger_pasif,
            side="pasif",
            instrument_type="diger_yukumluluk",
            islamic_class="Diğer",
            maturity_days=rng.randint(30, 180),
        ))
    
    return items


def generate_off_balance_sheet(
    seed: int = 42,
    total_assets_tl: float = 50_000_000_000,
) -> List[OffBalanceSheetItem]:
    """
    Bilanço dışı kalemleri üretir.
    Gayrinakdi krediler, Wa'd taahhütleri, Muwa'ada.
    """
    rng = random.Random(seed + 100)
    T = total_assets_tl
    items = []
    
    # Teminat Mektupları (%5-8 toplam aktifin)
    tm_ratio = rng.uniform(0.05, 0.08)
    items.append(OffBalanceSheetItem(
        name="Teminat Mektupları",
        amount=T * tm_ratio,
        currency="TL",
        item_type="teminat_mektubu",
        counterparty_type="kurumsal",
        maturity_days=rng.randint(90, 365),
        ccf=config.OFF_BALANCE_CCF["teminat_mektubu"],
    ))
    
    # Akreditifler (%2-4)
    ak_ratio = rng.uniform(0.02, 0.04)
    items.append(OffBalanceSheetItem(
        name="Akreditifler (İthalat/İhracat)",
        amount=T * ak_ratio,
        currency="USD",
        item_type="akreditif",
        counterparty_type="kurumsal",
        maturity_days=rng.randint(30, 180),
        ccf=config.OFF_BALANCE_CCF["akreditif"],
    ))
    
    # Wa'd Taahhütleri — Perakende (%3-5)
    wad_p = T * rng.uniform(0.03, 0.05)
    items.append(OffBalanceSheetItem(
        name="Wa'd Taahhütleri (Perakende - Kullanılmamış Limit)",
        amount=wad_p,
        currency="TL",
        item_type="wad_taahhut_perakende",
        counterparty_type="perakende",
        maturity_days=365,
        ccf=config.OFF_BALANCE_CCF["wad_taahhut_perakende"],
    ))
    
    # Wa'd Taahhütleri — Kurumsal (%2-4)
    wad_k = T * rng.uniform(0.02, 0.04)
    items.append(OffBalanceSheetItem(
        name="Wa'd Taahhütleri (Kurumsal)",
        amount=wad_k,
        currency="TL",
        item_type="wad_taahhut_kurumsal",
        counterparty_type="kurumsal",
        maturity_days=365,
        ccf=config.OFF_BALANCE_CCF["wad_taahhut_kurumsal"],
    ))
    
    # Wa'd Taahhütleri — Finansal Kuruluşlar (%1-2)
    wad_f = T * rng.uniform(0.01, 0.02)
    items.append(OffBalanceSheetItem(
        name="Wa'd Taahhütleri (Finansal Kuruluşlar)",
        amount=wad_f,
        currency="TL",
        item_type="wad_taahhut_finansal",
        counterparty_type="finansal",
        maturity_days=180,
        ccf=config.OFF_BALANCE_CCF["wad_taahhut_finansal"],
    ))
    
    # Muwa'ada (Karşılıklı Wa'd) (%0.5-1)
    muwada = T * rng.uniform(0.005, 0.01)
    items.append(OffBalanceSheetItem(
        name="Muwa'ada (Karşılıklı Taahhüt)",
        amount=muwada,
        currency="USD",
        item_type="muwada",
        counterparty_type="finansal",
        maturity_days=rng.randint(30, 90),
        ccf=config.OFF_BALANCE_CCF["muwada"],
    ))
    
    return items


def generate_cashflows(
    balance_sheet: List[BalanceSheetItem],
    months: int = 12,
    seed: int = 42,
) -> List[CashFlow]:
    """
    Bilanço kalemlerinden nakit akış verileri üretir.
    """
    rng = random.Random(seed + 200)
    cashflows = []
    today = date.today()
    
    for item in balance_sheet:
        if item.maturity_days <= 0 or item.maturity_days > months * 30:
            continue
        
        maturity_date = today + timedelta(days=item.maturity_days)
        
        if item.side == "aktif":
            # Anapara geri ödemesi (inflow)
            cashflows.append(CashFlow(
                date=maturity_date,
                amount=item.amount,
                currency=item.currency,
                direction="inflow",
                source_instrument=item.instrument_type,
                item_name=item.name,
            ))
            # Kâr payı gelirleri (aylık)
            if item.profit_rate > 0:
                monthly_income = item.amount * item.profit_rate / 12
                for m in range(1, min(item.maturity_days // 30 + 1, months + 1)):
                    cf_date = today + timedelta(days=30 * m)
                    cashflows.append(CashFlow(
                        date=cf_date,
                        amount=monthly_income,
                        currency=item.currency,
                        direction="inflow",
                        source_instrument=item.instrument_type,
                        item_name=f"{item.name} - Kâr Payı",
                    ))
        
        elif item.side == "pasif" and "ozkaynak" not in item.instrument_type:
            # Anapara geri ödemesi (outflow)
            cashflows.append(CashFlow(
                date=maturity_date,
                amount=item.amount,
                currency=item.currency,
                direction="outflow",
                source_instrument=item.instrument_type,
                item_name=item.name,
            ))
            # Kâr payı ödemeleri
            if item.profit_rate > 0:
                monthly_expense = item.amount * item.profit_rate / 12
                for m in range(1, min(item.maturity_days // 30 + 1, months + 1)):
                    cf_date = today + timedelta(days=30 * m)
                    cashflows.append(CashFlow(
                        date=cf_date,
                        amount=monthly_expense,
                        currency=item.currency,
                        direction="outflow",
                        source_instrument=item.instrument_type,
                        item_name=f"{item.name} - Kâr Payı",
                    ))
    
    return sorted(cashflows, key=lambda x: x.date)


def generate_profit_pools(
    balance_sheet: List[BalanceSheetItem],
    seed: int = 42,
) -> List[ProfitPool]:
    """
    Kâr payı havuz verilerini üretir.
    Her vade grubu için ayrı havuz oluşturulur.
    """
    rng = random.Random(seed + 300)
    pools = []
    
    # Pasif taraftaki vadeli katılma hesaplarını havuzlara ayır
    for tenor_key, tenor_info in config.PROFIT_POOL_TENORS.items():
        # Bu vade grubundaki katılma hesapları (fon kaynağı — pasif)
        pool_deposits = [
            i for i in balance_sheet
            if i.side == "pasif"
            and "katilma" in i.instrument_type
            and tenor_info["min_days"] <= i.maturity_days <= tenor_info["max_days"]
        ]
        
        total_funds = sum(i.amount for i in pool_deposits)
        if total_funds == 0:
            continue
        
        # Havuzdan kullandırım (fon kullanımı — aktif)
        utilization = rng.uniform(0.85, 0.98)
        total_placements = total_funds * utilization
        
        # Gelir hesabı
        avg_placement_rate = rng.uniform(0.38, 0.52)
        gross_income = total_placements * avg_placement_rate / 12  # Aylık
        expenses = gross_income * rng.uniform(0.03, 0.08)  # Operasyonel gider
        net_income = gross_income - expenses
        
        # Kâr dağıtımı
        alpha = rng.uniform(
            config.DCR_PARAMS["alpha_min"],
            config.DCR_PARAMS["alpha_max"]
        )
        bank_income = net_income * alpha
        customer_income = net_income * (1 - alpha)
        
        # Müşteriye verilen kâr payı oranı
        profit_rate = (customer_income * 12) / total_funds if total_funds > 0 else 0
        
        pools.append(ProfitPool(
            pool_name=f"{tenor_info['label']} Havuzu",
            tenor=tenor_key,
            total_funds=total_funds,
            total_placements=total_placements,
            gross_income=gross_income,
            expenses=expenses,
            net_income=net_income,
            bank_share_ratio=alpha,
            customer_share_ratio=1 - alpha,
            bank_income=bank_income,
            customer_income=customer_income,
            profit_rate=round(profit_rate, 4),
            fund_utilization=round(utilization * 100, 2),
        ))
    
    return pools


def generate_yield_curve(seed: int = 42) -> dict:
    """
    TCMB'ye yakın kâr payı oranı eğrisi üretir.
    
    Returns:
        dict: {vade_ay: oran} — Ör: {1: 0.42, 3: 0.43, 6: 0.44, ...}
    """
    rng = random.Random(seed + 400)
    base = rng.uniform(0.40, 0.48)
    
    curve = {}
    tenors = [1, 3, 6, 12, 24, 36, 60, 120]
    
    for i, tenor in enumerate(tenors):
        # Hafif yukarı eğimli eğri
        spread = i * rng.uniform(0.003, 0.008)
        curve[tenor] = round(base + spread, 4)
    
    return curve


def export_to_excel(
    balance_sheet: List[BalanceSheetItem],
    off_balance: List[OffBalanceSheetItem] = None,
    path: str = None,
):
    """
    Bilanço verilerini Excel dosyasına export eder.
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_balance_sheet.xlsx')
    
    # Dizini oluştur
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Bilanço DataFrame
    bs_data = []
    for item in balance_sheet:
        bs_data.append({
            "Kalem Adı": item.name,
            "Tutar (TL)": round(item.amount, 2),
            "Para Birimi": item.currency,
            "Orijinal Tutar": round(item.amount_original, 2),
            "Taraf": item.side,
            "Enstrüman Tipi": item.instrument_type,
            "İslami Sınıf": item.islamic_class,
            "Vade (Gün)": item.maturity_days,
            "Yeniden Fiyatlama (Gün)": item.repricing_days,
            "Kâr Payı Oranı": item.profit_rate,
            "Sigortalı": item.is_insured,
            "Karşı Taraf": item.counterparty_type,
            "Kredi Notu": item.credit_rating,
            "HQLA Seviye": item.hqla_level,
        })
    
    df_bs = pd.DataFrame(bs_data)
    
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df_bs.to_excel(writer, sheet_name='Bilanço', index=False)
        
        # Bilanço dışı kalemler
        if off_balance:
            obs_data = []
            for item in off_balance:
                obs_data.append({
                    "Kalem Adı": item.name,
                    "Tutar": round(item.amount, 2),
                    "Para Birimi": item.currency,
                    "Kalem Tipi": item.item_type,
                    "Karşı Taraf": item.counterparty_type,
                    "Vade (Gün)": item.maturity_days,
                    "Kredi Dönüşüm Faktörü": item.ccf,
                })
            df_obs = pd.DataFrame(obs_data)
            df_obs.to_excel(writer, sheet_name='Bilanço Dışı', index=False)
    
    return path


def balance_sheet_to_dataframe(items: List[BalanceSheetItem]) -> pd.DataFrame:
    """Bilanço kalemlerini pandas DataFrame'e çevirir."""
    data = []
    for item in items:
        data.append({
            "Kalem Adı": item.name,
            "Tutar (TL)": item.amount,
            "Para Birimi": item.currency,
            "Taraf": item.side,
            "Enstrüman Tipi": item.instrument_type,
            "İslami Sınıf": item.islamic_class,
            "Vade (Gün)": item.maturity_days,
            "Kâr Payı Oranı": item.profit_rate,
            "Karşı Taraf": item.counterparty_type,
            "HQLA": item.hqla_level,
        })
    return pd.DataFrame(data)


# Çalıştırılabilir: Örnek veri üret & kaydet
if __name__ == "__main__":
    print("📊 Katılım Bankası Örnek Bilanço Verisi Üretiliyor...")
    
    bs = generate_balance_sheet(seed=42)
    obs = generate_off_balance_sheet(seed=42)
    cf = generate_cashflows(bs)
    pools = generate_profit_pools(bs)
    curve = generate_yield_curve()
    
    # Aktif-Pasif dengesi kontrol
    aktif = sum(i.amount for i in bs if i.side == "aktif")
    pasif = sum(i.amount for i in bs if i.side == "pasif")
    
    print(f"\n{'='*50}")
    print(f"Toplam Aktif:  {aktif:>20,.0f} TL")
    print(f"Toplam Pasif:  {pasif:>20,.0f} TL")
    print(f"Fark:          {aktif - pasif:>20,.0f} TL")
    print(f"Bilanço Dışı:  {sum(i.amount for i in obs):>20,.0f} TL")
    print(f"Nakit Akış:    {len(cf):>20,} adet")
    print(f"Kâr Havuzları: {len(pools):>20}")
    print(f"{'='*50}")
    
    print("\n📈 Kâr Payı Eğrisi:")
    for tenor, rate in curve.items():
        print(f"  {tenor:>3} ay: %{rate*100:.2f}")
    
    print("\n💰 Kâr Payı Havuzları:")
    for pool in pools:
        print(f"  {pool.pool_name}: Fon={pool.total_funds:,.0f} TL, "
              f"Kâr Payı=%{pool.profit_rate*100:.2f}, Alpha={pool.bank_share_ratio:.2f}")
    
    # Excel kaydet
    path = export_to_excel(bs, obs)
    print(f"\n✅ Excel kaydedildi: {path}")
