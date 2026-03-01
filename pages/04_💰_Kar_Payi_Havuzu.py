# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Kâr Payı Havuzu & DCR Sayfası
Havuz performansı, kâr dağıtımı, DCR analizi, PER/IRR göstergeleri.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer

from components.sidebar import render_sidebar
from components.charts import create_pool_comparison_chart, COLORS
from components.metrics import render_kpi_card, render_traffic_light
from engines.profit_pool import calculate_all_pools, pool_transfer_pricing
from engines.dcr_engine import calculate_dcr, dcr_sensitivity_analysis, per_irr_adequacy
from engines.early_withdrawal import calculate_early_withdrawal_risk, get_early_withdrawal_summary
import config

st.set_page_config(page_title=f"{config.APP_TITLE} — Kâr Payı Havuzu", page_icon="💰", layout="wide")

data = render_sidebar()
bs = data["balance_sheet"]
pools_data = data["profit_pools"]

ozkaynak = sum(i.amount for i in bs if "ozkaynak" in i.instrument_type)

st.markdown("# 💰 Kâr Payı Havuzu & DCR Analizi")
st.markdown("Katılım bankasına özgü havuz bazlı kâr dağıtımı ve ticari kayma riski.")

# ==============================================================================
# Kâr Payı Havuzları
# ==============================================================================
st.markdown("---")
st.markdown("## 🏊 Kâr Payı Havuzu Performansı")

# Alpha oranı slider
alpha = st.slider(
    "Banka Payı (Alpha) Oranı",
    min_value=0.30, max_value=0.70, value=0.50, step=0.05,
    help="Bankanın net kâr payından aldığı pay oranı (Mudarib payı).",
    key="alpha_slider",
)

pool_result = calculate_all_pools(bs, alpha_by_tenor={t: alpha for t in config.PROFIT_POOL_TENORS})

# Havuz özet KPI'lar
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Toplam Fon", f"{pool_result.total_funds/1e9:,.1f} Mlyr TL", icon="💰")
with col2:
    render_kpi_card("Aylık Net Kâr", f"{pool_result.total_income/1e6:,.1f} M TL", icon="📈")
with col3:
    render_kpi_card("Ağırlıklı Kâr Payı", f"%{pool_result.weighted_avg_rate*100:.2f}", icon="📊")
with col4:
    render_kpi_card("Banka Payı / Müşteri Payı", 
                    f"{pool_result.total_bank_share/1e6:,.0f} / {pool_result.total_customer_share/1e6:,.0f} M TL", icon="⚖️")

# Havuz karşılaştırma grafiği
if pool_result.pools:
    fig = create_pool_comparison_chart(pool_result.pools)
    st.plotly_chart(fig, use_container_width=True)

# Havuz detay tablosu
if pool_result.pools:
    pool_data = {
        "Havuz": [p.pool_name for p in pool_result.pools],
        "Fon (M TL)": [round(p.total_funds / 1e6, 1) for p in pool_result.pools],
        "Kullandırım (M TL)": [round(p.total_placements / 1e6, 1) for p in pool_result.pools],
        "Fon Kullanım (%)": [p.fund_utilization for p in pool_result.pools],
        "Net Kâr (M TL)": [round(p.net_income / 1e6, 2) for p in pool_result.pools],
        "Alpha": [round(p.bank_share_ratio, 2) for p in pool_result.pools],
        "Müşteri Kâr Payı (%)": [round(p.profit_rate * 100, 2) for p in pool_result.pools],
    }
    st.dataframe(pool_data, use_container_width=True, hide_index=True)

# Pool Transfer Pricing
with st.expander("🔄 Havuzlar Arası Kaynak Aktarımı (Pool Transfer Pricing)"):
    if pool_result.pools:
        transfers = pool_transfer_pricing(pool_result.pools)
        if transfers:
            transfer_data = {
                "Havuz": [t["pool"] for t in transfers],
                "Durum": [t["type"].capitalize() for t in transfers],
                "Tutar (M TL)": [round(t["amount"] / 1e6, 1) for t in transfers],
                "İç Transfer Oranı": [round(t["internal_rate"] * 100, 2) for t in transfers],
                "Transfer Gelir/Gider (M TL)": [
                    round(t.get("transfer_income", t.get("transfer_cost", 0)) / 1e6, 2) for t in transfers
                ],
            }
            st.dataframe(transfer_data, use_container_width=True, hide_index=True)

# ==============================================================================
# DCR Analizi
# ==============================================================================
st.markdown("---")
st.markdown("## ⚠️ DCR — Displaced Commercial Risk (Ticari Kayma Riski)")
st.markdown("Bankanın rekabetçi kalabilmek için kendi kârından feragat etme riski.")

# Piyasa benchmark slider
market_rate = st.slider(
    "Piyasa Benchmark Kâr Payı Oranı (%)",
    min_value=20, max_value=60, value=45, step=1,
    key="market_rate",
) / 100

dcr_result = calculate_dcr(pool_result.pools, market_rate, ozkaynak)

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    status = "danger" if dcr_result.is_dcr_risk else "success"
    render_kpi_card("DCR Durumu", "RİSK VAR" if dcr_result.is_dcr_risk else "Güvenli", 
                    status=status, icon="⚠️")
    
    st.markdown(f"""
    | Gösterge | Değer |
    |----------|-------|
    | Piyasa Benchmark | %{dcr_result.market_benchmark_rate*100:.2f} |
    | Sunulan Oran | %{dcr_result.offered_rate*100:.2f} |
    | Spread | {dcr_result.spread*10000:.0f} bp |
    | DCR Maruz Kalım | {dcr_result.dcr_exposure/1e6:,.1f} M TL |
    """)

with col_d2:
    render_kpi_card("PER Bakiyesi", f"{dcr_result.per_balance/1e6:,.1f} M TL", icon="🛡️")
    render_kpi_card("IRR Bakiyesi", f"{dcr_result.irr_balance/1e6:,.1f} M TL", icon="🛡️")

with col_d3:
    # PER/IRR Yeterliliği
    adequacy = per_irr_adequacy(dcr_result)
    status_map = {"yeşil": "success", "sarı": "warning", "kırmızı": "danger"}
    render_kpi_card(
        "PER/IRR Yeterlilik", f"%{adequacy['coverage_ratio']:.1f}",
        status=status_map.get(adequacy["status"], "warning"), icon="📊"
    )
    st.info(f"💡 {adequacy['recommendation']}")

# DCR Hassasiyet
with st.expander("📊 DCR Hassasiyet Analizi"):
    dcr_sens = dcr_sensitivity_analysis(pool_result.pools, ozkaynak)
    dcr_df = pd.DataFrame(dcr_sens)
    st.dataframe(dcr_df, use_container_width=True, hide_index=True)

# ==============================================================================
# Erken Çekim Riski
# ==============================================================================
st.markdown("---")
st.markdown("## 🏃 Erken Çekim Riski")

stress_level = st.selectbox("Stres Seviyesi", [None, "hafif", "orta", "siddetli"], 
                            format_func=lambda x: "Baz Durum" if x is None else x.capitalize(),
                            key="ew_stress")

ew_results = calculate_early_withdrawal_risk(bs, stress_level=stress_level)
ew_summary = get_early_withdrawal_summary(ew_results)

col_ew1, col_ew2, col_ew3 = st.columns(3)
with col_ew1:
    render_kpi_card("Toplam Vadeli Katılma", f"{ew_summary['total_term_deposits']/1e9:,.1f} Mlyr TL", icon="💰")
with col_ew2:
    render_kpi_card("Beklenen Erken Çekim", f"{ew_summary['total_expected_withdrawal']/1e6:,.0f} M TL", icon="🏃")
with col_ew3:
    render_kpi_card("LCR Etkisi", f"{ew_summary['total_lcr_impact']/1e6:,.0f} M TL", 
                    status="warning" if ew_summary['total_lcr_impact'] > 0 else "success", icon="💧")

if ew_results:
    ew_data = {
        "Vade Grubu": [r.tenor for r in ew_results],
        "Toplam Mevduat (M TL)": [round(r.total_deposits / 1e6, 1) for r in ew_results],
        "Baz Olasılık (%)": [round(r.base_withdrawal_prob * 100, 2) for r in ew_results],
        "Stres Olasılık (%)": [round(r.stressed_withdrawal_prob * 100, 2) for r in ew_results],
        "Beklenen Çekim (M TL)": [round(r.expected_withdrawal / 1e6, 1) for r in ew_results],
        "Stres Çekim (M TL)": [round(r.stressed_withdrawal / 1e6, 1) for r in ew_results],
    }
    st.dataframe(ew_data, use_container_width=True, hide_index=True)
# Branding
render_footer()
render_developer_watermark()
