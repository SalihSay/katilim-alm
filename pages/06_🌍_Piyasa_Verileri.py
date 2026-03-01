# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Canlı Piyasa Verileri Sayfası
TCMB döviz kurları, faiz oranları, altın fiyatı ve verim eğrisi.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer
from components.explanations import render_chart_title
from engines.live_data import (
    fetch_all_market_data, get_fx_rate, build_live_yield_curve
)
import config

st.set_page_config(
    page_title=f"{config.APP_TITLE} — Piyasa Verileri",
    page_icon="🌍", layout="wide"
)

st.markdown("# 🌍 Canlı Piyasa Verileri")
st.markdown("TCMB'den anlık çekilen döviz kurları, faiz oranları ve verim eğrisi.")
st.caption("💡 Bu sayfadaki veriler TCMB'nin resmi XML API'sinden otomatik olarak çekilmektedir. Döviz kurları gün içinde güncellenir.")

# ==============================================================================
# Veri Çekme
# ==============================================================================

with st.spinner("📡 TCMB'den veriler çekiliyor..."):
    market = fetch_all_market_data()

if market.error:
    st.warning(f"⚠️ Veri çekme hatası: {market.error}. Fallback veriler gösteriliyor.")

# Durum bilgisi
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    status_icon = "🟢" if market.is_live else "🔴"
    st.markdown(f"**{status_icon} Veri Durumu:** {'Canlı' if market.is_live else 'Çevrimdışı'}")
with col_info2:
    st.markdown(f"**📅 Son Güncelleme:** {market.last_updated}")
with col_info3:
    st.markdown(f"**🏛️ Kaynak:** {market.data_source}")

if st.button("🔄 Verileri Yenile"):
    st.cache_data.clear()
    st.rerun()

# ==============================================================================
# 1. Döviz Kurları
# ==============================================================================
st.markdown("---")
render_chart_title("💱 Döviz Kurları", "TCMB günlük döviz kurları")
st.caption("Kaynak: tcmb.gov.tr/kurlar/today.xml — Her iş günü güncellenir")

if market.rates:
    # Ana kurlar
    main_currencies = ["USD", "EUR", "GBP", "CHF"]
    gulf_currencies = ["SAR", "KWD", "AED", "QAR"]

    # Ana Kurlar Cards
    st.markdown("#### 🏦 Ana Para Birimleri")
    cols = st.columns(len(main_currencies))
    for i, code in enumerate(main_currencies):
        rate = market.rates.get(code)
        if rate:
            with cols[i]:
                mid = (rate.forex_buying + rate.forex_selling) / 2
                spread = rate.forex_selling - rate.forex_buying
                st.markdown(f"""
<div style="background:linear-gradient(135deg,#1B2A4A,#2C3E6B);border-radius:10px;padding:16px;text-align:center;">
<div style="color:#D4AF37;font-size:12px;font-weight:600;">{rate.currency_name_tr}</div>
<div style="color:#fff;font-size:28px;font-weight:700;margin:6px 0;">₺{mid:.4f}</div>
<div style="color:#B0BEC5;font-size:11px;">Alış: {rate.forex_buying:.4f} | Satış: {rate.forex_selling:.4f}</div>
<div style="color:#888;font-size:10px;margin-top:4px;">Spread: {spread:.4f}</div>
</div>
""", unsafe_allow_html=True)

    # Altın
    xau = market.rates.get("XAU")
    if xau:
        st.markdown("#### 🥇 Altın Fiyatı")
        col_xau1, col_xau2, col_xau3, col_xau4 = st.columns(4)
        with col_xau1:
            mid_xau = (xau.forex_buying + xau.forex_selling) / 2
            st.metric("Altın (1 Ons / TL)", f"₺{mid_xau:,.2f}")
        with col_xau2:
            st.metric("Alış", f"₺{xau.forex_buying:,.2f}")
        with col_xau3:
            st.metric("Satış", f"₺{xau.forex_selling:,.2f}")
        with col_xau4:
            gram_gold = mid_xau / 31.1035  # 1 ons = 31.1035 gram
            st.metric("Gram Altın (yaklaşık)", f"₺{gram_gold:,.2f}")

    # Körfez Kurları (İslami Finans)
    st.markdown("#### 🕌 Körfez Ülkeleri (İslami Finans)")
    st.caption("Katılım bankacılığında önemli olan Körfez ülkesi para birimleri")
    gulf_data = []
    for code in gulf_currencies:
        rate = market.rates.get(code)
        if rate:
            gulf_data.append({
                "Para Birimi": f"{rate.currency_name_tr} ({code})",
                "Alış (TL)": f"{rate.forex_buying:.4f}",
                "Satış (TL)": f"{rate.forex_selling:.4f}",
                "Orta Kur": f"{(rate.forex_buying + rate.forex_selling)/2:.4f}",
            })
    if gulf_data:
        st.dataframe(pd.DataFrame(gulf_data), use_container_width=True, hide_index=True)

    # Tüm Kurlar Tablosu
    with st.expander("📋 Tüm Döviz Kurları Tablosu"):
        all_data = []
        for code, rate in sorted(market.rates.items()):
            all_data.append({
                "Kod": code,
                "Para Birimi": rate.currency_name_tr,
                "Birim": rate.unit,
                "Döviz Alış": f"{rate.forex_buying:.4f}",
                "Döviz Satış": f"{rate.forex_selling:.4f}",
                "Efektif Alış": f"{rate.banknote_buying:.4f}",
                "Efektif Satış": f"{rate.banknote_selling:.4f}",
            })
        st.dataframe(pd.DataFrame(all_data), use_container_width=True, hide_index=True)

else:
    st.error("Döviz kuru verisi çekilemedi.")

# ==============================================================================
# 2. Faiz / Kâr Payı Oranları
# ==============================================================================
st.markdown("---")
render_chart_title("📊 Faiz & Kâr Payı Oranları", "Politika faizi, gösterge tahvil, katılım oranları")

interest = market.interest

# Politika Faizi ve Enflasyon
col_r1, col_r2, col_r3, col_r4 = st.columns(4)
with col_r1:
    st.metric("🏛️ TCMB Politika Faizi", f"%{interest.policy_rate:.2f}")
with col_r2:
    st.metric("🌙 Gecelik Repo", f"%{interest.overnight_rate:.2f}")
with col_r3:
    st.metric("📈 Yıllık TÜFE", f"%{interest.cpi_annual:.2f}")
with col_r4:
    real_rate = interest.policy_rate - interest.cpi_annual
    st.metric("💰 Reel Faiz", f"%{real_rate:.2f}",
              delta=f"{'Pozitif' if real_rate > 0 else 'Negatif'}")

# Katılım Bankası Kâr Payı Oranları
st.markdown("#### 🕌 Katılım Bankası Kâr Payı Oranları")
st.caption("Katılım hesaplarına uygulanan kâr payı oranları (yıllık %)")

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.metric("1 Aylık", f"%{interest.participation_1m:.2f}")
with col_k2:
    st.metric("3 Aylık", f"%{interest.participation_3m:.2f}")
with col_k3:
    st.metric("6 Aylık", f"%{interest.participation_6m:.2f}")
with col_k4:
    st.metric("1 Yıllık", f"%{interest.participation_1y:.2f}")

# Devlet Tahvili Faizleri
st.markdown("#### 📜 Devlet İç Borçlanma Senetleri (DİBS)")
col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    st.metric("2 Yıllık DİBS", f"%{interest.gov_bond_2y:.2f}")
with col_d2:
    st.metric("5 Yıllık DİBS", f"%{interest.gov_bond_5y:.2f}")
with col_d3:
    st.metric("10 Yıllık DİBS", f"%{interest.gov_bond_10y:.2f}")

# ==============================================================================
# 3. Verim Eğrisi (Yield Curve)
# ==============================================================================
st.markdown("---")
render_chart_title("📈 Verim Eğrisi", "Vade bazlı getiri oranları")
st.caption("💡 Verim eğrisi, farklı vadelerdeki yatırım getiri oranlarını gösterir. Normal eğri yukarı eğimlidir (uzun vade = yüksek getiri). Ters eğri resesyon sinyali olabilir.")

yield_curve = build_live_yield_curve(interest)

# Verim eğrisi grafiği
tenors = list(yield_curve.keys())
rates_pct = [v * 100 for v in yield_curve.values()]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=tenors, y=rates_pct,
    mode='lines+markers',
    line=dict(color='#D4AF37', width=3),
    marker=dict(size=10, color='#1B2A4A', line=dict(width=2, color='#D4AF37')),
    name="Verim Eğrisi",
    hovertemplate='%{x}: %{y:.2f}%<extra></extra>',
))

# Politika faizi çizgisi
fig.add_hline(
    y=interest.policy_rate,
    line_dash="dash", line_color="#E74C3C",
    annotation_text=f"Politika Faizi: %{interest.policy_rate:.1f}",
    annotation_position="bottom right",
)

# TÜFE çizgisi
fig.add_hline(
    y=interest.cpi_annual,
    line_dash="dot", line_color="#F39C12",
    annotation_text=f"TÜFE: %{interest.cpi_annual:.1f}",
    annotation_position="top right",
)

fig.update_layout(
    height=400,
    font=dict(family="Inter"),
    xaxis_title="Vade",
    yaxis_title="Yıllık Getiri (%)",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(gridcolor='rgba(0,0,0,0.08)'),
    xaxis=dict(gridcolor='rgba(0,0,0,0.08)'),
)
st.plotly_chart(fig, use_container_width=True)

# Eğri Yorumu
if rates_pct[-1] > rates_pct[0]:
    st.success("📈 **Normal Verim Eğrisi** — Uzun vadeli getiriler kısa vadeden yüksek. Ekonomik büyüme beklentisi.")
elif rates_pct[-1] < rates_pct[0]:
    st.warning("📉 **Ters (Inverted) Verim Eğrisi** — Kısa vadeli getiriler uzun vadeden yüksek. Sıkılaştırma / resesyon sinyali olabilir.")
else:
    st.info("➡️ **Düz Verim Eğrisi** — Getiriler vade fark etmeksizin yakın seviyede.")

# ==============================================================================
# 4. FX Dönüştürücü
# ==============================================================================
st.markdown("---")
render_chart_title("🔄 Döviz Çevirici", "Canlı TCMB kurları ile dönüştürme")

col_conv1, col_conv2, col_conv3 = st.columns([2, 1, 2])
with col_conv1:
    amount = st.number_input("Tutar", value=1000000.0, step=100000.0, format="%.2f")
with col_conv2:
    available = [c for c in market.rates.keys() if c != "XAU"]
    from_curr = st.selectbox("Para Birimi", ["TL"] + sorted(available), index=1)
with col_conv3:
    if from_curr == "TL":
        for code in ["USD", "EUR", "GBP"]:
            rate = get_fx_rate(market, code)
            if rate > 0:
                st.metric(f"→ {code}", f"{amount / rate:,.2f} {code}")
    else:
        rate = get_fx_rate(market, from_curr)
        tl_val = amount * rate
        st.metric(f"→ TL", f"₺{tl_val:,.2f}")
        # USD çapraz kur
        usd_rate = get_fx_rate(market, "USD")
        if usd_rate > 0:
            st.metric(f"→ USD", f"${tl_val / usd_rate:,.2f}")

# ==============================================================================
# 5. ALM Etkisi Özeti
# ==============================================================================
st.markdown("---")
render_chart_title("🏦 ALM'ye Etkisi", "Canlı piyasa verilerinin bilançoya etkisi")

usd_rate = get_fx_rate(market, "USD")
eur_rate = get_fx_rate(market, "EUR")

st.markdown(f"""
| Gösterge | Değer | ALM Etkisi |
|----------|-------|------------|
| USD/TL | ₺{usd_rate:.4f} | Döviz varlık/borç değerlemesi, FX pozisyon hesabı |
| EUR/TL | ₺{eur_rate:.4f} | HQLA'daki EUR cinsi sukuk değerlemesi |
| Politika Faizi | %{interest.policy_rate:.2f} | DCR riski: Piyasa oranı yükselirse kâr payı baskısı |
| TÜFE | %{interest.cpi_annual:.2f} | Reel getiri hesabı, müşteri davranışı |
| 1 Ay Kâr Payı | %{interest.participation_1m:.2f} | Kısa vadeli katılma hesapları maliyeti |
| 1 Yıl Kâr Payı | %{interest.participation_1y:.2f} | Uzun vadeli fonlama maliyeti, NSFR etkisi |
| Verim Eğrisi | {'Normal ↗' if rates_pct[-1] > rates_pct[0] else 'Ters ↘'} | Duration gap stratejisi, IRRBB senaryoları |
""")

# Branding
render_footer()
render_developer_watermark()
