# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — LCR & NSFR Dashboard Sayfası
Para birimi bazlı LCR, HQLA dağılımı, waterfall chart, NSFR detay.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer
from components.explanations import render_metric_explanation, get_verdict, render_chart_title

from components.sidebar import render_sidebar
from components.charts import (
    create_gauge_chart, create_waterfall_chart,
    create_donut_chart, COLORS
)
from components.metrics import render_kpi_card, render_traffic_light
from engines.lcr_engine import calculate_lcr, calculate_lcr_by_currency
from engines.nsfr_engine import calculate_nsfr, get_nsfr_summary
import config

st.set_page_config(page_title=f"{config.APP_TITLE} — LCR & NSFR", page_icon="📊", layout="wide")

# Veri
data = render_sidebar()
bs = data["balance_sheet"]
obs = data["off_balance"]

st.markdown(f"# 📊 Likidite Oranları Analizi")
st.markdown("Bankanın kısa vadeli (LCR) ve uzun vadeli (NSFR) likidite yeterliliğinin detaylı analizi.")

# ==============================================================================
# LCR Bölümü
# ==============================================================================
st.markdown("---")
st.markdown("## 💧 LCR — Likidite Karşılama Oranı")
st.caption("💡 LCR, bankanın önümüzdeki 30 gün içinde tüm nakit çıkışlarını (müşteri mevduat çekimleri, borç ödemeleri vb.) karşılayacak yeterli likit varlığa sahip olup olmadığını ölçer. BDDK en az %100 olmasını zorunlu tutar.")

# Para birimi bazlı LCR
lcr_by_currency = calculate_lcr_by_currency(bs, obs)

tab_total, tab_tl, tab_yp = st.tabs(["📊 Toplam LCR", "🇹🇷 TL LCR", "💱 YP LCR"])

for tab, (currency, lcr_result) in zip(
    [tab_total, tab_tl, tab_yp],
    lcr_by_currency.items()
):
    with tab:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # HQLA Donut
            hqla_data = {
                "Level 1": lcr_result.hqla.level_1,
                "Level 2A": lcr_result.hqla.level_2a_after_haircut,
                "Level 2B": lcr_result.hqla.level_2b_after_haircut,
            }
            fig = create_donut_chart(hqla_data, f"HQLA Dağılımı ({currency})")
            st.plotly_chart(fig, use_container_width=True)
            
            # Gauge
            fig = create_gauge_chart(lcr_result.lcr_ratio, f"LCR ({currency})", 0, 250, 100)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Waterfall
            waterfall_data = {
                "HQLA": lcr_result.hqla.total_hqla / 1e6,
                "Nakit Çıkışlar": -lcr_result.total_outflows / 1e6,
                "Nakit Girişler": min(lcr_result.total_inflows, lcr_result.total_outflows * config.INFLOW_CAP) / 1e6,
                "Net Çıkışlar": 0,  # total marker
            }
            fig = create_waterfall_chart(waterfall_data, f"LCR Waterfall ({currency}) — Milyon TL")
            st.plotly_chart(fig, use_container_width=True)
            
            if lcr_result.inflow_cap_applied:
                st.warning(f"⚠️ Inflow cap uygulandı: Girişler çıkışların %75'i ile sınırlandı.")
        
        with col3:
            # KPI'lar
            status = "success" if lcr_result.is_compliant else "danger"
            render_kpi_card(f"LCR ({currency})", f"%{lcr_result.lcr_ratio:.1f}", target="Min: %100", status=status, icon="💧")
            
            st.markdown(f"""
            | Bileşen | Tutar (Milyon TL) |
            |---------|-------------------|
            | HQLA Toplam | {lcr_result.hqla.total_hqla/1e6:,.1f} |
            | Level 1 | {lcr_result.hqla.level_1/1e6:,.1f} |
            | Level 2A | {lcr_result.hqla.level_2a_after_haircut/1e6:,.1f} |
            | Level 2B | {lcr_result.hqla.level_2b_after_haircut/1e6:,.1f} |
            | Toplam Çıkışlar | {lcr_result.total_outflows/1e6:,.1f} |
            | Toplam Girişler | {lcr_result.total_inflows/1e6:,.1f} |
            | Net Çıkışlar | {lcr_result.net_outflows/1e6:,.1f} |
            """)

# Detay tablosu
with st.expander("📋 LCR Çıkış Detayları"):
    lcr_total = lcr_by_currency["TOTAL"]
    if lcr_total.outflow_detail:
        df = pd.DataFrame(lcr_total.outflow_detail)
        df["outflow_milyon"] = df["outflow"].apply(lambda x: round(x / 1e6, 2))
        df["amount_milyon"] = df["amount"].apply(lambda x: round(x / 1e6, 2))
        st.dataframe(
            df[["name", "amount_milyon", "runoff_rate", "outflow_milyon", "source"]].rename(columns={
                "name": "Kalem", "amount_milyon": "Tutar (M TL)", "runoff_rate": "Run-off",
                "outflow_milyon": "Çıkış (M TL)", "source": "Kaynak"
            }),
            use_container_width=True, hide_index=True,
        )

# ==============================================================================
# NSFR Bölümü
# ==============================================================================
st.markdown("---")
st.markdown("## 🏗️ NSFR — Net Kararılı Fonlama Oranı")
st.caption("💡 NSFR, bankanın uzun vadeli varlıklarını (örn: 5 yıllık konut finansmanı) uzun vadeli ve kararlı kaynaklarla (1 yıl+ mevduat, özkaynak) finanse edip edemediğini ölçer. Kısa vadeli mevduatla uzun vadeli kredi vermenin riskini gösterir.")

nsfr_result = calculate_nsfr(bs, obs)
nsfr_summary = get_nsfr_summary(nsfr_result)

col_n1, col_n2 = st.columns([1, 2])

with col_n1:
    fig = create_gauge_chart(nsfr_result.nsfr_ratio, "NSFR Oranı", 0, 250, 100)
    st.plotly_chart(fig, use_container_width=True)
    
    status = "success" if nsfr_result.is_compliant else "danger"
    render_kpi_card("NSFR", f"%{nsfr_result.nsfr_ratio:.1f}", target="Min: %100", status=status, icon="🏗️")

with col_n2:
    import plotly.graph_objects as go
    
    # ASF vs RSF karşılaştırma
    asf_cats = nsfr_summary["asf_by_category"]
    rsf_cats = nsfr_summary["rsf_by_category"]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="ASF (Stabil Fonlama)", 
        x=list(asf_cats.keys()), 
        y=[v["contribution"] / 1e6 for v in asf_cats.values()],
        marker_color=COLORS["success"], opacity=0.85,
    ))
    fig.update_layout(
        title="ASF Kategorilere Göre Dağılım (Milyon TL)",
        height=350, font=dict(family="Inter"), 
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

# NSFR Detay
with st.expander("📋 NSFR ASF / RSF Detayları"):
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**ASF (Kullanılabilir Kararılı Fonlama)**")
        st.caption("Özkaynak, uzun vadeli mevduat gibi kararlı kaynaklar. Ağırlık ne kadar yüksekse o kaynak o kadar karararlıdır.")
        if nsfr_result.asf.items_detail:
            df_asf = pd.DataFrame(nsfr_result.asf.items_detail)
            df_asf["amount_m"] = df_asf["amount"].apply(lambda x: round(x / 1e6, 1))
            df_asf["contribution_m"] = df_asf["contribution"].apply(lambda x: round(x / 1e6, 1))
            st.dataframe(
                df_asf[["name", "amount_m", "weight", "contribution_m"]].rename(columns={
                    "name": "Kalem", "amount_m": "Tutar (M TL)", "weight": "Ağırlık", "contribution_m": "Katkı (M TL)",
                }),
                use_container_width=True, hide_index=True,
            )
    with col_d2:
        st.markdown("**RSF (Gerekli Kararılı Fonlama)**")
        st.caption("Krediler, yatırımlar gibi varlıklarların gerektirdiği kararlı fonlama tutarı. Ağırlık yüksekse o varlık daha fazla kararlı fon ge rektirir.")
        if nsfr_result.rsf.items_detail:
            df_rsf = pd.DataFrame(nsfr_result.rsf.items_detail)
            df_rsf["amount_m"] = df_rsf["amount"].apply(lambda x: round(x / 1e6, 1))
            df_rsf["contribution_m"] = df_rsf["contribution"].apply(lambda x: round(x / 1e6, 1))
            st.dataframe(
                df_rsf[["name", "amount_m", "weight", "contribution_m"]].rename(columns={
                    "name": "Kalem", "amount_m": "Tutar (M TL)", "weight": "Ağırlık", "contribution_m": "Katkı (M TL)",
                }),
                use_container_width=True, hide_index=True,
            )

# Branding
render_footer()
render_developer_watermark()
