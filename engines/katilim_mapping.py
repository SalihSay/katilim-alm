# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — İslami Enstrüman → Basel III Mapping
Katılım bankası bilanço kalemlerini BDDK/Basel III kategorilerine eşleştirir.
Bu modül projenin en benzersiz bileşenidir.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import BalanceSheetItem, OffBalanceSheetItem
import config


# ==============================================================================
# HQLA Sınıflandırma
# ==============================================================================

# İslami enstrüman → HQLA Level mapping
HQLA_MAPPING = {
    # Level 1 — En yüksek kalite
    "nakit": "level_1",
    "merkez_bankasi": "level_1",
    "devlet_sukuk": "level_1",
    "devlet_kira_sertifikasi": "level_1",
    "tcmb_hesap": "level_1",
    
    # Level 2A — Yüksek kalite
    "ozel_sukuk_aa": "level_2a",        # AA- ve üstü kredi notu
    "belediye_sukuk": "level_2a",
    "kamu_sukuk": "level_2a",
    
    # Level 2B — Orta kalite
    "ozel_sukuk_diger": "level_2b",     # AA- altı kredi notu
    "kurumsal_sukuk": "level_2b",
    
    # HQLA Dışı
    "murabaha_alacak": "none",
    "finansal_kiralama": "none",
    "sabit_varlik": "none",
    "diger_aktif": "none",
}


def classify_hqla(item: BalanceSheetItem) -> str:
    """
    Bilanço kalemini HQLA seviyesine sınıflandırır.
    
    Returns:
        str: "level_1", "level_2a", "level_2b", veya "none"
    """
    instrument = item.instrument_type.lower()
    
    # Doğrudan mapping kontrolü
    if instrument in HQLA_MAPPING:
        return HQLA_MAPPING[instrument]
    
    # Kredi notuna göre Sukuk sınıflandırma
    if "sukuk" in instrument or "kira_sertifikasi" in instrument:
        if item.counterparty_type == "devlet":
            return "level_1"
        rating = item.credit_rating.upper()
        if rating in ["AAA", "AA+", "AA", "AA-"]:
            return "level_2a"
        return "level_2b"
    
    # Nakit ve merkez bankası
    if "nakit" in instrument or "kasa" in instrument:
        return "level_1"
    if "merkez" in instrument or "tcmb" in instrument:
        return "level_1"
    
    return "none"


def get_hqla_haircut(hqla_level: str) -> float:
    """HQLA seviyesine göre haircut oranını döndürür."""
    return config.HQLA_HAIRCUTS.get(hqla_level, 0.0)


# ==============================================================================
# LCR — Nakit Çıkış (Run-off) Oranları
# ==============================================================================

def get_runoff_rate(item: BalanceSheetItem) -> float:
    """
    Pasif kalem için nakit çıkış (run-off) oranını belirler.
    Katılım bankasına özgü: Katılma hesapları, Sukuk ihracı, vb.
    """
    instrument = item.instrument_type.lower()
    counterparty = item.counterparty_type.lower() if item.counterparty_type else ""
    
    # Katılma Hesapları (Perakende)
    if "katilma" in instrument or "katilim_hesabi" in instrument:
        if item.maturity_days == 0:  # Vadesiz
            if item.is_insured:
                return config.RUNOFF_RATES["katilma_vadesiz_sigortali"]
            return config.RUNOFF_RATES["katilma_vadesiz_sigortasiz"]
        else:  # Vadeli
            # Vadesi 30 gün içinde dolacak
            if item.maturity_days <= 30:
                return config.RUNOFF_RATES["katilma_vadeli_erken_cekim"]
            return config.RUNOFF_RATES["katilma_vadeli_normal"]
    
    # Bankalararası Murabaha Borçları
    if "bankalararasi" in instrument:
        if "operasyonel" in instrument:
            return config.RUNOFF_RATES["bankalararasi_murabaha_operasyonel"]
        return config.RUNOFF_RATES["bankalararasi_murabaha_diger"]
    
    # Kurumsal mevduat / katılma
    if counterparty in ["kurumsal", "corporate"]:
        if "operasyonel" in instrument:
            return config.RUNOFF_RATES["kurumsal_mevduat_operasyonel"]
        return config.RUNOFF_RATES["kurumsal_mevduat_diger"]
    
    # İhraç edilen Sukuk (vadesi 30 gün içinde)
    if "ihrac" in instrument and "sukuk" in instrument:
        if item.maturity_days <= 30:
            return 1.0  # Vadesi gelen Sukuk tam çıkış
        return 0.0
    
    # Varsayılan
    return 0.10


def get_off_balance_runoff(item: OffBalanceSheetItem) -> float:
    """Bilanço dışı kalem için nakit çıkış oranını belirler."""
    item_type = item.item_type.lower()
    counterparty = item.counterparty_type.lower() if item.counterparty_type else ""
    
    if "teminat_mektubu" in item_type:
        return config.RUNOFF_RATES["teminat_mektubu"]
    if "akreditif" in item_type:
        return config.RUNOFF_RATES["akreditif"]
    if "wad" in item_type:
        if counterparty == "perakende":
            return config.RUNOFF_RATES["wad_taahhut_perakende"]
        if counterparty == "finansal":
            return config.RUNOFF_RATES["wad_taahhut_finansal"]
        return config.RUNOFF_RATES["wad_taahhut_kurumsal"]
    
    return config.RUNOFF_RATES["gayrinakdi_diger"]


# ==============================================================================
# LCR — Nakit Giriş (Inflow) Oranları
# ==============================================================================

def get_inflow_rate(item: BalanceSheetItem) -> float:
    """
    Aktif kalem için nakit giriş oranını belirler.
    Sadece 30 gün içinde vadesi gelen alacaklar giriş olarak sayılır.
    """
    if item.maturity_days > 30:
        return 0.0
    
    instrument = item.instrument_type.lower()
    
    # Murabaha geri ödemeleri
    if "murabaha" in instrument:
        return config.INFLOW_RATES["murabaha_geri_odeme_30gun"]
    
    # Bankalararası alacaklar
    if "bankalararasi" in instrument:
        return config.INFLOW_RATES["bankalararasi_alacak"]
    
    # Sukuk kupon
    if "sukuk" in instrument or "kira_sertifikasi" in instrument:
        return config.INFLOW_RATES["sukuk_kupon"]
    
    return config.INFLOW_RATES["diger_alacak"]


# ==============================================================================
# NSFR — ASF Ağırlıkları
# ==============================================================================

def get_asf_weight(item: BalanceSheetItem) -> float:
    """
    Pasif kalem için Available Stable Funding (ASF) ağırlığını belirler.
    """
    instrument = item.instrument_type.lower()
    counterparty = item.counterparty_type.lower() if item.counterparty_type else ""
    
    # Özkaynaklar → %100
    if "ozkaynak" in instrument or "sermaye" in instrument:
        return config.ASF_WEIGHTS["ozkaynaklar"]
    
    # Vadeli Katılma Hesapları
    if "katilma" in instrument or "katilim_hesabi" in instrument:
        if item.maturity_days == 0:  # Vadesiz
            if counterparty in ["perakende", "retail", ""]:
                return config.ASF_WEIGHTS["vadesiz_katilma_perakende"]
            return config.ASF_WEIGHTS["vadesiz_katilma_kurumsal"]
        elif item.maturity_days > 365:
            return config.ASF_WEIGHTS["vadeli_katilma_1y_ustu"]
        elif item.maturity_days > 180:
            return config.ASF_WEIGHTS["vadeli_katilma_6_12ay"]
        else:
            return config.ASF_WEIGHTS["vadeli_katilma_0_6ay"]
    
    # İhraç edilen Sukuk
    if "ihrac" in instrument and "sukuk" in instrument:
        if item.maturity_days > 365:
            return config.ASF_WEIGHTS["ihrac_sukuk_1y_ustu"]
        elif item.maturity_days > 180:
            return config.ASF_WEIGHTS["ihrac_sukuk_6_12ay"]
        return 0.0
    
    # Bankalararası borçlar
    if "bankalararasi" in instrument:
        if item.maturity_days > 365:
            return config.ASF_WEIGHTS["bankalararasi_borc_1y_ustu"]
        elif item.maturity_days > 180:
            return config.ASF_WEIGHTS["bankalararasi_borc_6_12ay"]
        return config.ASF_WEIGHTS["bankalararasi_borc_0_6ay"]
    
    return 0.50  # Varsayılan


# ==============================================================================
# NSFR — RSF Ağırlıkları
# ==============================================================================

def get_rsf_weight(item: BalanceSheetItem) -> float:
    """
    Aktif kalem için Required Stable Funding (RSF) ağırlığını belirler.
    """
    instrument = item.instrument_type.lower()
    
    # Nakit → %0
    if "nakit" in instrument or "kasa" in instrument:
        return config.RSF_WEIGHTS["nakit"]
    
    # Merkez Bankası → %0
    if "merkez" in instrument or "tcmb" in instrument:
        return config.RSF_WEIGHTS["merkez_bankasi"]
    
    # Devlet Sukuk / Kira Sertifikası
    if ("devlet" in instrument or "kamu" in instrument) and ("sukuk" in instrument or "kira" in instrument):
        return config.RSF_WEIGHTS["devlet_sukuk_0_6ay"]  # Devlet Sukuk düşük RSF
    
    # Özel sektör Sukuk
    if "sukuk" in instrument or "kira_sertifikasi" in instrument:
        hqla = classify_hqla(item)
        if hqla == "level_2a":
            return config.RSF_WEIGHTS["ozel_sukuk_2a"]
        return config.RSF_WEIGHTS["ozel_sukuk_2b"]
    
    # Murabaha Alacakları
    if "murabaha" in instrument:
        if item.maturity_days > 365:
            return config.RSF_WEIGHTS["murabaha_alacak_1y_ustu"]
        return config.RSF_WEIGHTS["murabaha_alacak_0_6ay"]
    
    # Finansal Kiralama (İcara)
    if "kiralama" in instrument or "icara" in instrument:
        if item.maturity_days > 365:
            return config.RSF_WEIGHTS["finansal_kiralama_1y_ustu"]
        return config.RSF_WEIGHTS["finansal_kiralama_0_6ay"]
    
    # Sabit varlıklar → %100
    if "sabit" in instrument:
        return config.RSF_WEIGHTS["sabit_varliklar"]
    
    return config.RSF_WEIGHTS["diger_aktifler"]


# ==============================================================================
# Para Birimi Bazlı Sınıflandırma
# ==============================================================================

def is_foreign_currency(item) -> bool:
    """Kalemin yabancı para (YP) olup olmadığını kontrol eder."""
    return item.currency.upper() not in ["TL", "TRY"]


def is_gold(item) -> bool:
    """Kalemin altın (XAU) cinsinden olup olmadığını kontrol eder."""
    return item.currency.upper() in ["XAU", "ALTIN", "GOLD"]


def split_by_currency(items: list) -> dict:
    """
    Bilanço kalemlerini para birimine göre ayırır.
    
    Returns:
        dict: {"TL": [...], "YP": [...], "XAU": [...], "ALL": [...]}
    """
    result = {"TL": [], "YP": [], "XAU": [], "ALL": list(items)}
    
    for item in items:
        currency = item.currency.upper()
        if currency in ["TL", "TRY"]:
            result["TL"].append(item)
        elif currency in ["XAU", "ALTIN", "GOLD"]:
            result["XAU"].append(item)
        else:
            result["YP"].append(item)
    
    return result


# ==============================================================================
# Enstrüman Bilgi Fonksiyonları
# ==============================================================================

def get_instrument_description(instrument_type: str) -> str:
    """İslami enstrümanın Türkçe açıklamasını döndürür."""
    descriptions = {
        "nakit": "Nakit ve Kasa Mevcudu",
        "merkez_bankasi": "TCMB Nezdindeki Hesaplar",
        "devlet_sukuk": "Devlet Sukuk (Kira Sertifikası)",
        "devlet_kira_sertifikasi": "Devlet Kira Sertifikası",
        "ozel_sukuk_aa": "Özel Sektör Sukuk (Yüksek Derece)",
        "ozel_sukuk_diger": "Özel Sektör Sukuk (Diğer)",
        "murabaha_alacak": "Murabaha Alacakları (Maliyet + Kâr Marjı Satış)",
        "finansal_kiralama": "Finansal Kiralama (İcara) Alacakları",
        "bankalararasi_murabaha": "Bankalararası Murabaha (Plasman)",
        "sabit_varlik": "Sabit Varlıklar (Gayrimenkul, Ekipman)",
        "katilma_vadesiz": "Katılma Hesabı (Vadesiz — Cari Hesap)",
        "katilma_vadeli": "Katılma Hesabı (Vadeli — Kâr/Zarar Ortaklığı)",
        "ihrac_sukuk": "İhraç Edilen Sukuk (Kira Sertifikası)",
        "bankalararasi_borc": "Bankalararası Murabaha Borçları",
        "ozkaynaklar": "Özkaynaklar (Ana Sermaye + Yedekler)",
        "wad_taahhut": "Wa'd Taahhütleri (Tek Taraflı Söz)",
        "muwada": "Muwa'ada (Karşılıklı Söz)",
        "teminat_mektubu": "Teminat Mektubu (Garanti)",
        "akreditif": "Akreditif (İthalat/İhracat Garantisi)",
    }
    return descriptions.get(instrument_type.lower(), instrument_type)


def get_basel3_equivalent(instrument_type: str) -> str:
    """İslami enstrümanın konvansiyonel Basel III karşılığını döndürür."""
    equivalents = {
        "nakit": "Nakit",
        "merkez_bankasi": "Merkez Bankası Rezervleri",
        "devlet_sukuk": "Devlet Tahvili",
        "devlet_kira_sertifikasi": "Devlet Tahvili",
        "ozel_sukuk_aa": "Yüksek Dereceli Kurumsal Bono",
        "ozel_sukuk_diger": "Kurumsal Bono",
        "murabaha_alacak": "Ticari Kredi",
        "finansal_kiralama": "Finansal Kiralama Alacağı",
        "bankalararasi_murabaha": "Bankalararası Plasman",
        "katilma_vadesiz": "Vadesiz Mevduat",
        "katilma_vadeli": "Vadeli Mevduat",
        "ihrac_sukuk": "Banka Bonosu / Tahvil İhracı",
        "bankalararasi_borc": "Bankalararası Borçlanma",
        "ozkaynaklar": "Özkaynaklar",
        "wad_taahhut": "Kullanılmamış Kredi Limiti",
        "muwada": "Forwards / Türev Taahhüt",
        "teminat_mektubu": "Garanti / Kefalet",
        "akreditif": "Akreditif",
    }
    return equivalents.get(instrument_type.lower(), "Diğer")
