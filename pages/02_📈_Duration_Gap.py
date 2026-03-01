# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Duration & Gap Analizi Sayfası
Duration karşılaştırma, repricing gap tablosu, IRRBB 6 senaryo heatmap.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer

from components.sidebar import render_sidebar
from components.charts import create_gap_bar_chart, create_heatmap, COLORS
from components.metrics import render_kpi_card
from engines.duration_calc import portfolio_duration, duration_gap, equity_value_change
from engines.gap_analysis import build_gap_table, calculate_nii_impact, get_gap_summary
from engines.irrbb import run_irrbb_analysis, build_yield_curve
import config

st.set_page_config(page_title=f"{config.APP_TITLE} — Duration & Gap", page_icon="📈", layout="wide")

data = render_sidebar()
bs = data["balance_sheet"]
curve = data["yield_curve"]

st.markdown("# 📈 Vade Riski & Oran Değişim Analizi")
st.markdown("Varlık ve borçların vade yapısı, oran değişimlerine duyarlılık ve risk ölçümü.")

# ==============================================================================
# Duration
# ==============================================================================
st.markdown("---")
st.markdown("## 📐 Vade Uyumsuzluğu (Duration Gap) Analizi")
st.caption("💡 Duration, bir varlığın veya borcun ortalama geri ödeme süresini yıl olarak gösterir. Aktif ve pasif duration arasındaki fark (gap), kâr payı oranları değiştiğinde bankanın ne kadar etkileneceğini belirler.")

total_aktif = sum(i.amount for i in bs if i.side == "aktif")
total_pasif = sum(i.amount for i in bs if i.side == "pasif")
ozkaynak = sum(i.amount for i in bs if "ozkaynak" in i.instrument_type)

a_dur = portfolio_duration(bs, "aktif")
p_dur = portfolio_duration(bs, "pasif")
dur_gap_val = duration_gap(a_dur, p_dur, total_aktif, total_pasif)

col1, col2, col3, col4 = st.columns(4)

with col1:
    render_kpi_card("Aktif Ortalama Vade", f"{a_dur:.2f} yıl", icon="📊")
with col2:
    render_kpi_card("Pasif Ortalama Vade", f"{p_dur:.2f} yıl", icon="📊")
with col3:
    dur_status = "success" if abs(dur_gap_val) < 2 else ("warning" if abs(dur_gap_val) < 4 else "danger")
    render_kpi_card("Vade Farkı (Gap)", f"{dur_gap_val:.2f} yıl", status=dur_status, icon="📐")
with col4:
    # Duration Gap yorumu
    if dur_gap_val > 0:
        st.info("📈 **Pozitif Gap**: Kâr payı oranları yükselirse özkaynak değer kaybeder.")
    elif dur_gap_val < 0:
        st.info("📉 **Negatif Gap**: Kâr payı oranları düşerse özkaynak değer kaybeder.")
    else:
        st.success("✅ **Nötr**: Duration dengeli.")

# İnteraktif slider
st.markdown("### 🏛️ Kâr Payı Oranı Değişse Ne Olur?")
st.caption("💡 Slider'ı kaydırarak farklı kâr payı oranı değişimlerinde bankanın özkaynak değerinin ne kadar etkileneceğini görün. +100bp = %1 oran artışı.")
shock_bp = st.slider("Kâr payı oranı değişimi (baz puan)", -500, 500, 100, step=50, key="dur_shock")
delta_y = shock_bp / 10000
eve_change = equity_value_change(dur_gap_val, total_aktif, delta_y)

col_s1, col_s2 = st.columns(2)
with col_s1:
    change_pct = (eve_change / ozkaynak * 100) if ozkaynak > 0 else 0
    color = "🔴" if eve_change < 0 else "🟢"
    st.metric(
        f"Özkaynak Değer Değişimi ({shock_bp:+d}bp)",
        f"{eve_change/1e6:,.1f} Milyon TL",
        f"{change_pct:+.2f}%"
    )
with col_s2:
    st.metric(
        "Stres Sonrası Özkaynak",
        f"{(ozkaynak + eve_change)/1e6:,.1f} Milyon TL",
        f"{eve_change/1e6:+,.1f} M TL"
    )

# ==============================================================================
# Gap Analizi
# ==============================================================================
st.markdown("---")
st.markdown("## 📊 Vade Aralığı Analizi (Repricing Gap)")
st.caption("💡 Varlık ve borçlar, yeniden fiyatlama vadelerine göre 7 aralığa ayrılır. Her aralıkta varlıklar borçlardan fazlaysa 'fazla' (yeşil), azsa 'açık' (kırmızı) vardır.")

gap_table = build_gap_table(bs)
gap_summary = get_gap_summary(gap_table)

# Gap bar chart
fig = create_gap_bar_chart(gap_table)
st.plotly_chart(fig, use_container_width=True)

# Gap tablosu
gap_data = {
    "Vade Aralığı": [g.bucket_name for g in gap_table],
    "Kâr Payına Duyarlı Varlıklar (M TL)": [round(g.rate_sensitive_assets / 1e6, 1) for g in gap_table],
    "Kâr Payına Duyarlı Borçlar (M TL)": [round(g.rate_sensitive_liabilities / 1e6, 1) for g in gap_table],
    "Açık/Fazla (M TL)": [round(g.gap / 1e6, 1) for g in gap_table],
    "Birikimli Açık (M TL)": [round(g.cumulative_gap / 1e6, 1) for g in gap_table],
    "Aktife Oran (%)": [round(g.gap_to_total_assets, 2) for g in gap_table],
}
st.dataframe(gap_data, use_container_width=True, hide_index=True)

# NII etkisi
col_nii1, col_nii2 = st.columns(2)
with col_nii1:
    nii_up = gap_summary.get("nii_100bp_up", 0)
    st.metric("Oranlar %1 Yükselirse Net Gelir Etkisi", f"{nii_up/1e6:,.1f} Milyon TL")
with col_nii2:
    nii_down = gap_summary.get("nii_100bp_down", 0)
    st.metric("Oranlar %1 Düşerse Net Gelir Etkisi", f"{nii_down/1e6:,.1f} Milyon TL")

# ==============================================================================
# IRRBB
# ==============================================================================
st.markdown("---")
st.markdown("## 🔥 Kâr Payı Oranı Riski (IRRBB)")
st.caption("💡 Basel standardı 6 farklı şok senaryosu uygulayarak kâr payı oranları değiştiğinde bankanın özkaynak değerinin (ΔEVE) ve net gelirinin (ΔNII) ne kadar etkileneceğini hesaplar. ΔEVE özkaynaklara oranı %15'i aşmamalıdır.")

yield_curve = build_yield_curve()
irrbb_results = run_irrbb_analysis(bs, yield_curve, ozkaynak)

# IRRBB tablosu
irrbb_data = {
    "Senaryo": [r.scenario_name for r in irrbb_results],
    "Baz EVE (M TL)": [round(r.base_eve / 1e6, 1) for r in irrbb_results],
    "Şok EVE (M TL)": [round(r.shocked_eve / 1e6, 1) for r in irrbb_results],
    "ΔEVE (M TL)": [round(r.delta_eve / 1e6, 1) for r in irrbb_results],
    "ΔEVE/Özkaynak (%)": [r.delta_eve_pct for r in irrbb_results],
    "ΔNII (M TL)": [round(r.delta_nii / 1e6, 1) for r in irrbb_results],
    "ΔNII/NII (%)": [r.delta_nii_pct for r in irrbb_results],
}
st.dataframe(irrbb_data, use_container_width=True, hide_index=True)

# Heatmap
heatmap_data = [
    {"scenario_name": r.scenario_name, "delta_eve_pct": r.delta_eve_pct, "delta_nii_pct": r.delta_nii_pct}
    for r in irrbb_results
]
fig = create_heatmap(heatmap_data, "IRRBB Heatmap — Senaryo Bazlı Etki")
st.plotly_chart(fig, use_container_width=True)
# Branding
render_footer()
render_developer_watermark()
