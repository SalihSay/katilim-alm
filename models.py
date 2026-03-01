# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Veri Modelleri
Tüm veri yapıları @dataclass ile tanımlanır.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import date


# ==============================================================================
# Temel Bilanço Modelleri
# ==============================================================================

@dataclass
class BalanceSheetItem:
    """Bilanço kalemi."""
    name: str                           # Kalem adı (ör: "Murabaha Alacakları")
    amount: float                       # Tutar (TL cinsinden)
    currency: str = "TL"                # Para birimi: TL, USD, EUR, XAU
    amount_original: float = 0.0        # Orijinal para birimi cinsinden tutar
    side: str = "aktif"                 # "aktif" veya "pasif"
    instrument_type: str = ""           # İslami enstrüman tipi
    islamic_class: str = ""             # İslami sınıf (ör: Murabaha, Sukuk, İcara)
    maturity_days: int = 0              # Kalan vade (gün)
    repricing_days: int = 0             # Yeniden fiyatlama vadesi (gün)
    profit_rate: float = 0.0            # Kâr payı oranı (yıllık)
    is_insured: bool = False            # TMSF sigortalı mı?
    counterparty_type: str = ""         # Karşı taraf: perakende, kurumsal, finansal, devlet
    credit_rating: str = ""             # Kredi notu (AAA, AA, A, BBB, vb.)
    hqla_level: str = ""                # HQLA seviyesi: level_1, level_2a, level_2b, none
    

@dataclass
class CashFlow:
    """Nakit akış kalemi."""
    date: date                          # Nakit akış tarihi
    amount: float                       # Tutar
    currency: str = "TL"
    direction: str = "inflow"           # "inflow" veya "outflow"
    source_instrument: str = ""         # Kaynak enstrüman
    item_name: str = ""                 # İlgili bilanço kalemi adı


@dataclass
class OffBalanceSheetItem:
    """Bilanço dışı kalem."""
    name: str                           # Kalem adı
    amount: float                       # Nominal tutar
    currency: str = "TL"
    item_type: str = ""                 # teminat_mektubu, akreditif, wad_taahhut, muwada, vb.
    counterparty_type: str = ""         # perakende, kurumsal, finansal
    maturity_days: int = 0
    ccf: float = 0.0                    # Kredi Dönüşüm Faktörü
    

# ==============================================================================
# LCR Modelleri
# ==============================================================================

@dataclass
class HQLABreakdown:
    """HQLA detay dökümü."""
    level_1: float = 0.0
    level_2a_gross: float = 0.0
    level_2a_after_haircut: float = 0.0
    level_2b_gross: float = 0.0
    level_2b_after_haircut: float = 0.0
    total_before_cap: float = 0.0
    level_2_cap_adjustment: float = 0.0
    level_2b_cap_adjustment: float = 0.0
    total_hqla: float = 0.0
    items_detail: list = field(default_factory=list)


@dataclass
class LCRResult:
    """LCR hesaplama sonucu."""
    hqla: HQLABreakdown = field(default_factory=HQLABreakdown)
    total_outflows: float = 0.0
    total_inflows: float = 0.0
    inflow_cap_applied: bool = False
    net_outflows: float = 0.0
    lcr_ratio: float = 0.0
    is_compliant: bool = False
    currency: str = "TOTAL"             # TOTAL, TL, veya YP
    outflow_detail: list = field(default_factory=list)
    inflow_detail: list = field(default_factory=list)


# ==============================================================================
# NSFR Modelleri
# ==============================================================================

@dataclass
class ASFBreakdown:
    """Available Stable Funding detayı."""
    total_asf: float = 0.0
    items_detail: list = field(default_factory=list)  # (kalem, tutar, ağırlık, katkı)


@dataclass
class RSFBreakdown:
    """Required Stable Funding detayı."""
    total_rsf: float = 0.0
    items_detail: list = field(default_factory=list)


@dataclass
class NSFRResult:
    """NSFR hesaplama sonucu."""
    asf: ASFBreakdown = field(default_factory=ASFBreakdown)
    rsf: RSFBreakdown = field(default_factory=RSFBreakdown)
    nsfr_ratio: float = 0.0
    is_compliant: bool = False


# ==============================================================================
# Duration & Gap Modelleri
# ==============================================================================

@dataclass
class DurationResult:
    """Duration hesaplama sonucu."""
    macaulay_duration: float = 0.0
    modified_duration: float = 0.0
    convexity: float = 0.0
    item_name: str = ""


@dataclass
class GapBucket:
    """Gap analizi vade aralığı."""
    bucket_name: str = ""               # "0-1 Ay", "1-3 Ay", vb.
    min_days: int = 0
    max_days: int = 0
    rate_sensitive_assets: float = 0.0   # RSA
    rate_sensitive_liabilities: float = 0.0  # RSL
    gap: float = 0.0                    # RSA - RSL
    cumulative_gap: float = 0.0
    gap_to_total_assets: float = 0.0    # Gap / Toplam Aktif (%)


@dataclass
class IRRBBResult:
    """IRRBB analiz sonucu."""
    scenario_name: str = ""
    base_eve: float = 0.0               # Baz durum ekonomik değer
    shocked_eve: float = 0.0            # Şok sonrası ekonomik değer
    delta_eve: float = 0.0              # ΔEVE
    delta_eve_pct: float = 0.0          # ΔEVE / Özkaynak (%)
    base_nii: float = 0.0               # Baz durum net kâr payı geliri
    shocked_nii: float = 0.0
    delta_nii: float = 0.0              # ΔNII
    delta_nii_pct: float = 0.0          # ΔNII / NII (%)


# ==============================================================================
# Stres Testi Modelleri
# ==============================================================================

@dataclass
class StressScenario:
    """Stres testi senaryo tanımı."""
    name: str = ""
    fx_shock: float = 0.0               # FX şoku (ör: 0.20 = %20 değer kaybı)
    rate_shock_bp: int = 0              # Kâr payı şoku (baz puan)
    deposit_runoff: float = 0.0         # Mevduat kaçış oranı
    credit_loss: float = 0.0            # Kredi değer kaybı oranı
    description: str = ""


@dataclass
class StressResult:
    """Stres testi sonucu."""
    scenario: StressScenario = field(default_factory=StressScenario)
    base_lcr: float = 0.0
    stressed_lcr: float = 0.0
    base_nsfr: float = 0.0
    stressed_nsfr: float = 0.0
    base_leverage: float = 0.0
    stressed_leverage: float = 0.0
    base_duration_gap: float = 0.0
    stressed_duration_gap: float = 0.0
    lcr_impact: float = 0.0             # LCR değişimi
    nsfr_impact: float = 0.0
    lcr_compliant: bool = False
    nsfr_compliant: bool = False
    leverage_compliant: bool = False


# ==============================================================================
# Kâr Payı Havuzu Modelleri
# ==============================================================================

@dataclass
class ProfitPool:
    """Kâr payı havuzu."""
    pool_name: str = ""                 # Havuz adı (ör: "1 Ay Havuzu")
    tenor: str = ""                     # Vade grubu (1_ay, 3_ay, vb.)
    total_funds: float = 0.0            # Havuzdaki toplam fon
    total_placements: float = 0.0       # Havuzdan kullandırılan tutar
    gross_income: float = 0.0           # Brüt kâr (gelir)
    expenses: float = 0.0              # Giderler
    net_income: float = 0.0             # Net kâr
    bank_share_ratio: float = 0.50      # Banka payı (alpha)
    customer_share_ratio: float = 0.50  # Müşteri payı (1-alpha)
    bank_income: float = 0.0            # Banka kâr payı
    customer_income: float = 0.0        # Müşteri kâr payı
    profit_rate: float = 0.0            # Müşteriye dağıtılan kâr payı oranı
    fund_utilization: float = 0.0       # Fon kullanım oranı (%)


@dataclass
class ProfitPoolResult:
    """Kâr payı havuzu genel sonuç."""
    pools: list = field(default_factory=list)  # list[ProfitPool]
    total_funds: float = 0.0
    total_income: float = 0.0
    weighted_avg_rate: float = 0.0      # Ağırlıklı ortalama kâr payı
    total_bank_share: float = 0.0
    total_customer_share: float = 0.0


# ==============================================================================
# DCR (Displaced Commercial Risk) Modelleri
# ==============================================================================

@dataclass
class DCRResult:
    """Displaced Commercial Risk sonucu."""
    market_benchmark_rate: float = 0.0  # Piyasa benchmark oranı
    offered_rate: float = 0.0           # Bankanın sunduğu oran
    spread: float = 0.0                 # Fark (piyasa - sunulan)
    dcr_exposure: float = 0.0           # DCR maruz kalım tutarı
    per_balance: float = 0.0            # Profit Equalization Reserve bakiyesi
    irr_balance: float = 0.0            # Investment Risk Reserve bakiyesi
    per_contribution: float = 0.0       # Dönem PER katkısı
    irr_contribution: float = 0.0       # Dönem IRR katkısı
    alpha_current: float = 0.0          # Mevcut alpha oranı
    alpha_required: float = 0.0         # DCR'yi karşılamak için gereken alpha
    is_dcr_risk: bool = False           # DCR riski var mı?
    dcr_impact_on_equity: float = 0.0   # Özkaynak etkisi


# ==============================================================================
# Kaldıraç Oranı Modeli
# ==============================================================================

@dataclass
class LeverageRatioResult:
    """Kaldıraç oranı sonucu."""
    tier1_capital: float = 0.0          # Çekirdek sermaye
    on_balance_exposure: float = 0.0    # Bilanço içi risk
    off_balance_exposure: float = 0.0   # Bilanço dışı risk (CCF uygulanmış)
    total_exposure: float = 0.0         # Toplam risk tutarı
    leverage_ratio: float = 0.0         # Kaldıraç oranı (%)
    is_compliant: bool = False
    detail: list = field(default_factory=list)


# ==============================================================================
# Erken Çekim Riski Modeli
# ==============================================================================

@dataclass
class EarlyWithdrawalResult:
    """Erken çekim riski analiz sonucu."""
    tenor: str = ""                     # Vade grubu
    total_deposits: float = 0.0         # Toplam vadeli katılma
    base_withdrawal_prob: float = 0.0   # Baz erken çekim olasılığı
    stressed_withdrawal_prob: float = 0.0  # Stres altında olasılık
    expected_withdrawal: float = 0.0    # Beklenen erken çekim tutarı
    stressed_withdrawal: float = 0.0    # Stres altında çekim tutarı
    lcr_impact: float = 0.0            # LCR üzerindeki etki
    items: list = field(default_factory=list)  # Detay
