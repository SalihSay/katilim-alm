# ==============================================================================
# KatılımALM — © 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazılım telif hakları ile korunmaktadır.
# İzinsiz kopyalanması, dağıtılması veya değiştirilmesi yasaktır.
# ==============================================================================
"""
KatılımALM — Ana Dashboard Giriş Noktası
Katılım Bankası Bilanço & Likidite Risk Dashboard'u
© 2024-2026 Salih Say — Tüm hakları saklıdır.
"""
import streamlit as st
import sys, os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from components.sidebar import render_sidebar
from components.metrics import render_kpi_card
from components.charts import create_gauge_chart, COLORS
from components.branding import render_developer_watermark, render_footer
from components.explanations import (
    render_executive_summary, get_verdict, render_metric_explanation, render_chart_title
)
from engines.lcr_engine import calculate_lcr
from engines.nsfr_engine import calculate_nsfr
from engines.leverage_ratio import calculate_leverage_ratio
from engines.duration_calc import portfolio_duration, duration_gap
from engines.data_generator import balance_sheet_to_dataframe

# ==============================================================================
# Sayfa Konfigürasyonu
# ==============================================================================
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# CSS
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main > div {
    padding-top: 1rem;
}

h1, h2, h3, h4 {
    color: #1B2A4A;
    font-weight: 700;
}

.stMetric {
    background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%);
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

div[data-testid="stSidebarContent"] {
    background: linear-gradient(180deg, #F8F9FA 0%, #EAECEE 100%);
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# Sidebar & Veri Yükleme
# ==============================================================================
data = render_sidebar()
bs = data["balance_sheet"]
obs = data["off_balance"]
pools = data["profit_pools"]
curve = data["yield_curve"]
bank_name = data["bank_name"]
report_date = data["report_date"]

# Session state'e kaydet (sayfalar arası paylaşım)
# Not: bank_name ve report_date widget key'leri ile çakışmaması için farklı isim
st.session_state["bs_data"] = bs
st.session_state["obs_data"] = obs
st.session_state["pools_data"] = pools
st.session_state["curve_data"] = curve
st.session_state["current_bank_name"] = bank_name
st.session_state["current_report_date"] = report_date

# ==============================================================================
# Hesaplamalar
# ==============================================================================
lcr_result = calculate_lcr(bs, obs)
nsfr_result = calculate_nsfr(bs, obs)
leverage_result = calculate_leverage_ratio(bs, obs)

total_aktif = sum(i.amount for i in bs if i.side == "aktif")
total_pasif = sum(i.amount for i in bs if i.side == "pasif")
a_dur = portfolio_duration(bs, "aktif")
p_dur = portfolio_duration(bs, "pasif")
dur_gap = duration_gap(a_dur, p_dur, total_aktif, total_pasif)

# FX pozisyon
fx_aktif = sum(i.amount for i in bs if i.side == "aktif" and i.currency not in ["TL", "TRY"])
fx_pasif = sum(i.amount for i in bs if i.side == "pasif" and i.currency not in ["TL", "TRY"])
ozkaynak = sum(i.amount for i in bs if "ozkaynak" in i.instrument_type)
fx_pozisyon = ((fx_aktif - fx_pasif) / ozkaynak * 100) if ozkaynak > 0 else 0

# ==============================================================================
# Ana Sayfa İçeriği
# ==============================================================================

# Başlık
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {COLORS['primary']} 0%, #2C3E6B 100%);
    padding: 24px 30px;
    border-radius: 12px;
    margin-bottom: 20px;
">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: {COLORS['accent']}; margin: 0; font-size: 28px;">
                {config.APP_ICON} {config.APP_TITLE}
            </h1>
            <p style="color: #B0BEC5; margin: 6px 0 0 0; font-size: 14px;">
                {config.APP_SUBTITLE}
            </p>
        </div>
        <div style="text-align: right;">
            <div style="color: #B0BEC5; font-size: 12px;">{bank_name}</div>
            <div style="color: {COLORS['accent']}; font-size: 16px; font-weight: 600;">
                {report_date.strftime('%d.%m.%Y')}
            </div>
            <div style="color: #B0BEC5; font-size: 11px;">
                Toplam Aktif: {total_aktif/1e9:,.1f} Milyar TL
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5-SANİYE KURALI: YÖNETİCİ ÖZETİ
# ==========================================
st.markdown("### 🎯 Genel Durum — Tek Bakışta")
render_executive_summary(
    lcr_result.lcr_ratio,
    nsfr_result.nsfr_ratio,
    leverage_result.leverage_ratio,
    dur_gap,
    fx_pozisyon
)

# ==========================================
# KPI Kartları + Anlık Yorum
# ==========================================
st.markdown("### 📊 Temel Göstergeler")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    lcr_status = "success" if lcr_result.lcr_ratio >= 100 else ("warning" if lcr_result.lcr_ratio >= 80 else "danger")
    render_kpi_card(
        "Likidite (LCR)", f"%{lcr_result.lcr_ratio:.1f}",
        target="BDDK Min: %100", status=lcr_status, icon="💧"
    )

with col2:
    nsfr_status = "success" if nsfr_result.nsfr_ratio >= 100 else ("warning" if nsfr_result.nsfr_ratio >= 80 else "danger")
    render_kpi_card(
        "Fonlama (NSFR)", f"%{nsfr_result.nsfr_ratio:.1f}",
        target="BDDK Min: %100", status=nsfr_status, icon="🏗️"
    )

with col3:
    dur_status = "success" if abs(dur_gap) < 2 else ("warning" if abs(dur_gap) < 4 else "danger")
    render_kpi_card(
        "Vade Riski", f"{dur_gap:.2f} yıl",
        status=dur_status, icon="📐"
    )

with col4:
    fx_status = "success" if abs(fx_pozisyon) < config.FX_POSITION_LIMIT else "danger"
    render_kpi_card(
        "Kur Riski", f"%{fx_pozisyon:.1f}",
        target=f"Limit: %{config.FX_POSITION_LIMIT:.0f}", status=fx_status, icon="💱"
    )

with col5:
    lev_status = "success" if leverage_result.leverage_ratio >= 3 else "danger"
    render_kpi_card(
        "Sermaye", f"%{leverage_result.leverage_ratio:.1f}",
        target="Min: %3", status=lev_status, icon="⚖️"
    )

# Verdicts (anlık yorumlar)
st.markdown(f"""
<div style="
    background: #F8F9FA; border-radius: 8px; padding: 10px 16px; 
    margin: 4px 0 16px 0; font-size: 12px; line-height: 1.8;
">
    {get_verdict('lcr', lcr_result.lcr_ratio)}<br>
    {get_verdict('nsfr', nsfr_result.nsfr_ratio)}<br>
    {get_verdict('leverage', leverage_result.leverage_ratio)}<br>
    {get_verdict('duration_gap', dur_gap)}
</div>
""", unsafe_allow_html=True)

# ==========================================
# Gauge Grafikler + Açıklamalar
# ==========================================
col_g1, col_g2, col_g3 = st.columns(3)

with col_g1:
    render_chart_title("Likidite Oranı", "30 günlük nakit yeterliliği")
    fig = create_gauge_chart(lcr_result.lcr_ratio, "LCR", 0, 250, 100)
    st.plotly_chart(fig, use_container_width=True)
    render_metric_explanation("lcr")

with col_g2:
    render_chart_title("Fonlama Oranı", "Uzun vadeli kaynak yeterliliği")
    fig = create_gauge_chart(nsfr_result.nsfr_ratio, "NSFR", 0, 250, 100)
    st.plotly_chart(fig, use_container_width=True)
    render_metric_explanation("nsfr")

with col_g3:
    render_chart_title("Sermaye Gücü", "Sermaye / toplam varlık")
    fig = create_gauge_chart(leverage_result.leverage_ratio, "Kaldıraç", 0, 15, 3)
    st.plotly_chart(fig, use_container_width=True)
    render_metric_explanation("leverage")

# ==========================================
# Bilanço Özeti (sadeleştirilmiş)
# ==========================================
st.markdown("### 📋 Bilanço Özeti")
st.caption("Bankanın varlıkları (aktifler) ve kaynakları (pasifler). Detaylı düzenleme için sol menüdeki '✏️ Bilanço Düzenleme' sayfasını kullanın.")

col_b1, col_b2 = st.columns(2)

with col_b1:
    st.markdown("**📗 AKTİFLER (Varlıklar)**")
    aktif_items = [i for i in bs if i.side == "aktif"]
    aktif_data = {
        "Kalem Adı": [i.name for i in aktif_items],
        "Tutar (Milyon TL)": [f"{i.amount / 1e6:,.1f}" for i in aktif_items],
        "Para Birimi": [i.currency for i in aktif_items],
    }
    st.dataframe(aktif_data, use_container_width=True, hide_index=True)

with col_b2:
    st.markdown("**📕 PASİFLER (Kaynaklar)**")
    pasif_items = [i for i in bs if i.side == "pasif"]
    pasif_data = {
        "Kalem Adı": [i.name for i in pasif_items],
        "Tutar (Milyon TL)": [f"{i.amount / 1e6:,.1f}" for i in pasif_items],
        "Para Birimi": [i.currency for i in pasif_items],
    }
    st.dataframe(pasif_data, use_container_width=True, hide_index=True)

# Footer & Branding
render_footer()
render_developer_watermark()

