# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Canlı Piyasa Verileri
TCMB ve diğer kaynaklardan gerçek zamanlı veri çekme.

Veri Kaynakları:
  1. TCMB Döviz Kurları (XML, API key gerektirmez)
  2. TCMB Altın Fiyatları (XML)
  3. TCMB Politika Faizi & Gösterge Tahvil Faizi
  4. TCMB EVDS (Elektronik Veri Dağıtım Sistemi)
"""
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import json
import streamlit as st


# ==============================================================================
# Veri Modelleri
# ==============================================================================

@dataclass
class ExchangeRate:
    """Döviz kuru bilgisi."""
    currency_code: str          # USD, EUR, GBP, XAU...
    currency_name_tr: str       # ABD Doları, Euro...
    forex_buying: float         # Döviz alış
    forex_selling: float        # Döviz satış
    banknote_buying: float      # Efektif alış
    banknote_selling: float     # Efektif satış
    unit: int = 1               # Birim (genelde 1)
    date: str = ""              # Tarih


@dataclass
class InterestRates:
    """Faiz/kâr payı oranları."""
    policy_rate: float = 0.0            # TCMB politika faizi (%)
    overnight_rate: float = 0.0         # Gecelik faiz (%)
    gov_bond_2y: float = 0.0            # 2 yıllık DİBS faizi
    gov_bond_5y: float = 0.0            # 5 yıllık DİBS faizi
    gov_bond_10y: float = 0.0           # 10 yıllık DİBS faizi
    participation_1m: float = 0.0       # Katılım bankası 1 ay kâr payı
    participation_3m: float = 0.0       # 3 ay
    participation_6m: float = 0.0       # 6 ay
    participation_1y: float = 0.0       # 1 yıl
    cpi_annual: float = 0.0             # Yıllık TÜFE (%)
    date: str = ""


@dataclass
class MarketData:
    """Tüm piyasa verilerini bir arada tutan model."""
    rates: Dict[str, ExchangeRate] = field(default_factory=dict)
    interest: InterestRates = field(default_factory=InterestRates)
    last_updated: str = ""
    data_source: str = ""
    is_live: bool = False
    error: str = ""


# ==============================================================================
# TCMB Döviz Kurları
# ==============================================================================

def _try_import_requests():
    """requests modülünü import et, yoksa urllib kullan."""
    try:
        import requests
        return requests
    except ImportError:
        return None


@st.cache_data(ttl=3600)  # 1 saat cache
def fetch_tcmb_exchange_rates() -> Dict[str, ExchangeRate]:
    """
    TCMB günlük döviz kurlarını çeker.
    Kaynak: https://www.tcmb.gov.tr/kurlar/today.xml
    API key gerektirmez, ücretsiz.
    """
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    rates = {}

    try:
        requests = _try_import_requests()
        if requests:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            xml_data = resp.content
        else:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as resp:
                xml_data = resp.read()

        root = ET.fromstring(xml_data)
        report_date = root.attrib.get("Tarih", "")

        # İlgili para birimleri
        target_currencies = {
            "USD", "EUR", "GBP", "CHF", "JPY",
            "SAR", "KWD", "AED", "QAR",  # Körfez ülkeleri (İslami finans)
            "CAD", "AUD", "NOK", "SEK", "DKK",
            "XAU",  # Altın
        }

        for currency in root.findall("Currency"):
            code = currency.attrib.get("CurrencyCode", "")

            if code not in target_currencies:
                continue

            def safe_float(tag):
                elem = currency.find(tag)
                if elem is not None and elem.text:
                    return float(elem.text)
                return 0.0

            unit_elem = currency.find("Unit")
            unit = int(unit_elem.text) if unit_elem is not None and unit_elem.text else 1

            rate = ExchangeRate(
                currency_code=code,
                currency_name_tr=currency.findtext("Isim", ""),
                forex_buying=safe_float("ForexBuying"),
                forex_selling=safe_float("ForexSelling"),
                banknote_buying=safe_float("BanknoteBuying"),
                banknote_selling=safe_float("BanknoteSelling"),
                unit=unit,
                date=report_date,
            )
            rates[code] = rate

    except Exception as e:
        # Hata durumunda fallback veriler
        rates["_error"] = ExchangeRate(
            currency_code="ERR", currency_name_tr=str(e),
            forex_buying=0, forex_selling=0,
            banknote_buying=0, banknote_selling=0,
        )

    return rates


# ==============================================================================
# TCMB Faiz Oranları (Fallback: son bilinen değerler)
# ==============================================================================

@st.cache_data(ttl=86400)  # 24 saat cache
def fetch_interest_rates() -> InterestRates:
    """
    Güncel faiz oranlarını çeker.
    TCMB EVDS API'den veya fallback olarak son bilinen değerleri kullanır.

    Not: EVDS API key gerektirir. Key yoksa güncel referans oranları kullanılır.
    EVDS API key almak için: https://evds2.tcmb.gov.tr/ adresinden kayıt olunabilir.
    """
    rates = InterestRates()

    # TCMB EVDS API denemesi (key varsa)
    evds_key = ""
    try:
        evds_key = st.secrets.get("TCMB_EVDS_KEY", "")
    except Exception:
        evds_key = ""

    if evds_key:
        try:
            rates = _fetch_from_evds(evds_key)
            rates.date = datetime.now().strftime("%d.%m.%Y")
            return rates
        except Exception:
            pass

    # Fallback: Mart 2026 referans oranları
    rates.policy_rate = 42.50       # TCMB politika faizi
    rates.overnight_rate = 44.00    # Gecelik repo
    rates.gov_bond_2y = 30.00       # 2Y DİBS
    rates.gov_bond_5y = 28.50       # 5Y DİBS
    rates.gov_bond_10y = 27.00      # 10Y DİBS
    rates.participation_1m = 38.00  # Katılım 1 ay kâr payı
    rates.participation_3m = 40.00  # 3 ay
    rates.participation_6m = 35.00  # 6 ay
    rates.participation_1y = 33.00  # 1 yıl
    rates.cpi_annual = 39.05        # Yıllık TÜFE
    rates.date = datetime.now().strftime("%d.%m.%Y")

    return rates


def _fetch_from_evds(api_key: str) -> InterestRates:
    """TCMB EVDS API'den faiz verisi çek."""
    import requests

    rates = InterestRates()
    base_url = "https://evds2.tcmb.gov.tr/service/evds"

    today = datetime.now()
    start = (today - timedelta(days=30)).strftime("%d-%m-%Y")
    end = today.strftime("%d-%m-%Y")

    # Politika faizi serisi
    series = "TP.PF.PF"  # Politika faizi
    params = {
        "series": series,
        "startDate": start,
        "endDate": end,
        "type": "json",
        "key": api_key,
    }

    resp = requests.get(base_url, params=params, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        if items:
            last = items[-1]
            val = last.get(series.replace(".", "_"), "")
            if val:
                rates.policy_rate = float(val)

    return rates


# ==============================================================================
# Tüm Piyasa Verisini Birleştir
# ==============================================================================

def fetch_all_market_data() -> MarketData:
    """Tüm canlı piyasa verilerini çeker ve birleştirir."""
    market = MarketData()

    # Döviz kurları
    rates = fetch_tcmb_exchange_rates()
    if "_error" in rates:
        market.error = rates["_error"].currency_name_tr
        del rates["_error"]

    market.rates = rates
    market.is_live = len(rates) > 0

    # Faiz oranları
    market.interest = fetch_interest_rates()

    # Meta
    market.last_updated = datetime.now().strftime("%d.%m.%Y %H:%M")
    market.data_source = "TCMB (tcmb.gov.tr)"

    return market


def get_fx_rate(market: MarketData, currency: str) -> float:
    """Belirli bir para birimi için orta kur döndürür."""
    if currency in ("TL", "TRY"):
        return 1.0
    rate = market.rates.get(currency)
    if rate:
        return (rate.forex_buying + rate.forex_selling) / 2
    return 0.0


def convert_to_tl(amount: float, currency: str, market: MarketData) -> float:
    """Herhangi bir tutarı TL'ye çevirir (canlı kur ile)."""
    fx = get_fx_rate(market, currency)
    return amount * fx


# ==============================================================================
# Yield Curve (Verim Eğrisi) — Canlı Veriden
# ==============================================================================

def build_live_yield_curve(interest: InterestRates) -> dict:
    """Canlı faiz verilerinden verim eğrisi oluşturur."""
    return {
        "1M": interest.participation_1m / 100,
        "3M": interest.participation_3m / 100,
        "6M": interest.participation_6m / 100,
        "1Y": interest.participation_1y / 100,
        "2Y": interest.gov_bond_2y / 100,
        "5Y": interest.gov_bond_5y / 100,
        "10Y": interest.gov_bond_10y / 100,
    }
