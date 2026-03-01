# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Konfigürasyon & Sabitler
BDDK Basel III parametreleri, katılım bankası referans değerleri ve stres senaryoları.
"""

# ==============================================================================
# BDDK Basel III — Asgari Oranlar
# ==============================================================================
LCR_MIN_RATIO = 100.0           # Asgari LCR oranı (%)
NSFR_MIN_RATIO = 100.0          # Asgari NSFR oranı (%)
LEVERAGE_RATIO_MIN = 3.0        # Asgari kaldıraç oranı (%)
FX_POSITION_LIMIT = 20.0        # Net FX pozisyon / özkaynaklar (%)

# ==============================================================================
# LCR — HQLA Parametreleri
# ==============================================================================
HQLA_HAIRCUTS = {
    "level_1": 0.00,            # Devlet Sukuk, TCMB, Nakit
    "level_2a": 0.15,           # Yüksek dereceli özel sektör Sukuk (AA-)
    "level_2b": 0.50,           # Diğer özel sektör Sukuk
}

# HQLA Kompozisyon Limitleri
HQLA_LEVEL2_CAP = 0.40         # Level 2 varlıklar ≤ HQLA'nın %40'ı
HQLA_LEVEL2B_CAP = 0.15        # Level 2B varlıklar ≤ HQLA'nın %15'i

# ==============================================================================
# LCR — Nakit Çıkış (Run-off) Oranları
# ==============================================================================
RUNOFF_RATES = {
    # Katılma Hesapları (Perakende)
    "katilma_vadesiz_sigortali": 0.05,
    "katilma_vadesiz_sigortasiz": 0.10,
    "katilma_vadeli_erken_cekim": 0.10,
    "katilma_vadeli_normal": 0.05,
    # Toptan Fonlama
    "bankalararasi_murabaha_operasyonel": 0.25,
    "bankalararasi_murabaha_diger": 0.40,
    "kurumsal_mevduat_operasyonel": 0.25,
    "kurumsal_mevduat_diger": 0.40,
    # Taahhütler
    "wad_taahhut_perakende": 0.05,
    "wad_taahhut_kurumsal": 0.10,
    "wad_taahhut_finansal": 0.40,
    # Bilanço dışı
    "teminat_mektubu": 0.05,
    "akreditif": 0.05,
    "gayrinakdi_diger": 0.05,
}

# ==============================================================================
# LCR — Nakit Giriş (Inflow) Oranları
# ==============================================================================
INFLOW_RATES = {
    "murabaha_geri_odeme_30gun": 0.50,
    "bankalararasi_alacak": 1.00,
    "sukuk_kupon": 1.00,
    "diger_alacak": 0.50,
}
INFLOW_CAP = 0.75              # Inflow cap: Toplam girişler ≤ çıkışların %75'i

# ==============================================================================
# NSFR — ASF Ağırlıkları (Available Stable Funding)
# ==============================================================================
ASF_WEIGHTS = {
    "ozkaynaklar": 1.00,
    "vadeli_katilma_1y_ustu": 1.00,
    "vadeli_katilma_6_12ay": 0.50,
    "vadeli_katilma_0_6ay": 0.00,          # <6ay → kararsız
    "vadesiz_katilma_perakende": 0.90,
    "vadesiz_katilma_kurumsal": 0.50,
    "ihrac_sukuk_1y_ustu": 1.00,
    "ihrac_sukuk_6_12ay": 0.50,
    "bankalararasi_borc_1y_ustu": 1.00,
    "bankalararasi_borc_6_12ay": 0.50,
    "bankalararasi_borc_0_6ay": 0.00,
}

# ==============================================================================
# NSFR — RSF Ağırlıkları (Required Stable Funding)
# ==============================================================================
RSF_WEIGHTS = {
    "nakit": 0.00,
    "merkez_bankasi": 0.00,
    "devlet_sukuk_0_6ay": 0.05,
    "devlet_sukuk_6_12ay": 0.05,
    "devlet_sukuk_1y_ustu": 0.05,
    "ozel_sukuk_2a": 0.15,
    "ozel_sukuk_2b": 0.50,
    "murabaha_alacak_0_6ay": 0.50,
    "murabaha_alacak_6_12ay": 0.50,
    "murabaha_alacak_1y_ustu": 0.85,
    "finansal_kiralama_0_6ay": 0.50,
    "finansal_kiralama_1y_ustu": 0.85,
    "sabit_varliklar": 1.00,
    "diger_aktifler": 1.00,
    # Bilanço dışı
    "gayrinakdi_rsf": 0.05,
}

# ==============================================================================
# Duration & IRRBB Parametreleri
# ==============================================================================
PARALLEL_SHIFT_BP = [100, 200, -100, -200]

# BDDK/Basel Standart IRRBB Şok Senaryoları (baz puan)
IRRBB_SCENARIOS = {
    "Paralel Yukarı":       {"short": 200, "long": 200},
    "Paralel Aşağı":        {"short": -200, "long": -200},
    "Eğim Dikleşme":        {"short": -100, "long": 100},
    "Eğim Düzleşme":        {"short": 100, "long": -100},
    "Kısa Vade Yukarı":     {"short": 250, "long": 0},
    "Kısa Vade Aşağı":      {"short": -250, "long": 0},
}

# Gap Analizi Vade Aralıkları (gün cinsinden)
GAP_BUCKETS = [
    {"name": "0-1 Ay", "min_days": 0, "max_days": 30},
    {"name": "1-3 Ay", "min_days": 31, "max_days": 90},
    {"name": "3-6 Ay", "min_days": 91, "max_days": 180},
    {"name": "6-12 Ay", "min_days": 181, "max_days": 365},
    {"name": "1-2 Yıl", "min_days": 366, "max_days": 730},
    {"name": "2-5 Yıl", "min_days": 731, "max_days": 1825},
    {"name": "5+ Yıl", "min_days": 1826, "max_days": 99999},
]

# ==============================================================================
# Katılım Bankası — Kâr Payı Referansları
# ==============================================================================
DEFAULT_PROFIT_RATE = 0.45      # Katılma hesabı referans kâr payı oranı (yıllık)
MURABAHA_MARGIN = 0.03          # Murabaha marjı
SUKUK_YIELD = 0.40              # Devlet Sukuk kâr payı (yıllık)

# Kâr Payı Havuzu Vade Grupları
PROFIT_POOL_TENORS = {
    "1_ay": {"min_days": 1, "max_days": 30, "label": "1 Ay"},
    "3_ay": {"min_days": 31, "max_days": 90, "label": "3 Ay"},
    "6_ay": {"min_days": 91, "max_days": 180, "label": "6 Ay"},
    "1_yil": {"min_days": 181, "max_days": 365, "label": "1 Yıl"},
    "1_yil_ustu": {"min_days": 366, "max_days": 99999, "label": "1 Yıl+"},
}

# ==============================================================================
# DCR — Displaced Commercial Risk Parametreleri
# ==============================================================================
DCR_PARAMS = {
    "alpha_min": 0.30,          # Bankanın minimum kâr payı (Mudarib payı)
    "alpha_max": 0.70,          # Bankanın maksimum kâr payı
    "alpha_default": 0.50,      # Varsayılan alpha oranı
    "per_rate": 0.01,           # Profit Equalization Reserve (gelirin %1'i)
    "irr_rate": 0.005,          # Investment Risk Reserve (gelirin %0.5'i)
    "per_max_ratio": 0.05,      # PER / toplam katılma hesabı max oranı
    "irr_max_ratio": 0.03,      # IRR / toplam katılma hesabı max oranı
    "market_benchmark_spread": 0.02,  # Piyasa benchmarkından sapma eşiği
}

# ==============================================================================
# Kaldıraç Oranı Parametreleri
# ==============================================================================
LEVERAGE_PARAMS = {
    "min_ratio": 3.0,           # Asgari %3
    "ccf_teminat_mektubu": 0.20,  # Kredi Dönüşüm Faktörü
    "ccf_akreditif": 0.20,
    "ccf_wad_taahhut": 0.10,
    "ccf_gayrinakdi_diger": 0.10,
}

# ==============================================================================
# Bilanço Dışı Kalemler — Kredi Dönüşüm Faktörleri (CCF)
# ==============================================================================
OFF_BALANCE_CCF = {
    "teminat_mektubu": 1.00,    # Tam dönüşüm (LCR için)
    "akreditif": 1.00,
    "wad_taahhut_perakende": 0.05,
    "wad_taahhut_kurumsal": 0.10,
    "wad_taahhut_finansal": 0.40,
    "muwada": 0.50,             # Karşılıklı Wa'd
    "gayrinakdi_diger": 0.05,
}

# ==============================================================================
# Erken Çekim Riski Parametreleri
# ==============================================================================
EARLY_WITHDRAWAL_PARAMS = {
    "base_probability": {        # Vade bazlı baz erken çekim olasılığı
        "1_ay": 0.02,
        "3_ay": 0.05,
        "6_ay": 0.08,
        "1_yil": 0.12,
        "1_yil_ustu": 0.15,
    },
    "stress_multiplier": {       # Stres altında çarpan
        "hafif": 1.5,
        "orta": 2.0,
        "siddetli": 3.0,
    },
    "rate_sensitivity": 0.5,     # Kâr payı oranı değişimine hassasiyet
}

# ==============================================================================
# Stres Senaryoları Varsayılanları
# ==============================================================================
STRESS_SCENARIOS = {
    "Hafif": {
        "fx_shock": 0.10,
        "rate_shock_bp": 200,
        "deposit_runoff": 0.05,
        "credit_loss": 0.02,
        "description": "Hafif ekonomik yavaşlama",
    },
    "Orta": {
        "fx_shock": 0.20,
        "rate_shock_bp": 400,
        "deposit_runoff": 0.10,
        "credit_loss": 0.05,
        "description": "Orta düzey ekonomik kriz",
    },
    "Şiddetli": {
        "fx_shock": 0.40,
        "rate_shock_bp": 800,
        "deposit_runoff": 0.20,
        "credit_loss": 0.10,
        "description": "Şiddetli finansal kriz",
    },
    "2018 Krizi": {
        "fx_shock": 0.35,
        "rate_shock_bp": 1000,
        "deposit_runoff": 0.15,
        "credit_loss": 0.08,
        "description": "2018 Ağustos kur krizi benzeri",
    },
    "2021 Krizi": {
        "fx_shock": 0.50,
        "rate_shock_bp": 600,
        "deposit_runoff": 0.25,
        "credit_loss": 0.06,
        "description": "2021 Aralık kur şoku benzeri",
    },
}

# ==============================================================================
# Para Birimleri
# ==============================================================================
CURRENCIES = ["TL", "USD", "EUR", "XAU"]  # XAU = Altın
DEFAULT_CURRENCY = "TL"

# FX Kurları (varsayılan)
DEFAULT_FX_RATES = {
    "USD_TL": 32.50,
    "EUR_TL": 35.20,
    "XAU_TL": 2150.00,          # 1 gram altın
}

# ==============================================================================
# UI Sabitleri
# ==============================================================================
APP_TITLE = "KatılımALM"
APP_ICON = "🏦"
APP_SUBTITLE = "Katılım Bankası Bilanço & Likidite Risk Dashboard'u"
THEME_PRIMARY_COLOR = "#1B2A4A"     # Koyu lacivert
THEME_ACCENT_COLOR = "#D4AF37"      # Altın
THEME_SUCCESS_COLOR = "#2ECC71"     # Yeşil
THEME_WARNING_COLOR = "#F39C12"     # Sarı
THEME_DANGER_COLOR = "#E74C3C"      # Kırmızı
