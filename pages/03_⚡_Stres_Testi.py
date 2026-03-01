# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Stres Testi Sayfası
Senaryo seçici, slider'lar, tornado chart, trafik ışıkları.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer

from components.sidebar import render_sidebar
from components.charts import (
    create_tornado_chart, create_stress_comparison_chart, COLORS
)
from components.metrics import render_kpi_card, render_comparison_card, render_traffic_light
from engines.stress_test import (
    run_stress_scenario, compare_scenarios,
    sensitivity_analysis, load_preset_scenarios
)
from engines.scenario_engine import create_scenario
from models import StressScenario
import config

st.set_page_config(page_title=f"{config.APP_TITLE} — Stres Testi", page_icon="⚡", layout="wide")

data = render_sidebar()
bs = data["balance_sheet"]
obs = data["off_balance"]

st.markdown("# ⚡ Stres Testi & Senaryo Analizi")
st.markdown("Çeşitli kriz durumlarında (kur şoku, mevduat kaçışı, kâr payı artışı) banka oranlarının nasıl etkileneceğini simüle eder.")
st.caption("💡 Stres testi, gerçek hayatta yaşanmış krizlerin (2018 kur krizi, 2021 faiz artışı gibi) tekrar yaşanması durumunda bankanın dayanabilirliğini ölçer. Sonuçta LCR ve NSFR oranlarının yasal limitleri aşıp aşmadığına bakılır.")

# ==============================================================================
# Senaryo Seçimi
# ==============================================================================
st.markdown("---")

tab_preset, tab_custom, tab_compare = st.tabs([
    "📋 Öntanımlı Senaryolar", "🎛️ Özel Senaryo", "📊 Karşılaştırma"
])

with tab_preset:
    st.markdown("### Öntanımlı Stres Senaryoları")
    
    scenario_name = st.selectbox(
        "Senaryo seçin:",
        list(config.STRESS_SCENARIOS.keys()),
        key="preset_scenario",
    )
    
    params = config.STRESS_SCENARIOS[scenario_name]
    
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric("FX Şoku", f"%{params['fx_shock']*100:.0f}")
    with col_p2:
        st.metric("Kâr Payı Şoku", f"{params['rate_shock_bp']}bp")
    with col_p3:
        st.metric("Mevduat Kaçışı", f"%{params['deposit_runoff']*100:.0f}")
    with col_p4:
        st.metric("Kredi Kaybı", f"%{params['credit_loss']*100:.0f}")
    
    st.markdown(f"*{params.get('description', '')}*")
    
    scenario = StressScenario(
        name=scenario_name,
        fx_shock=params["fx_shock"],
        rate_shock_bp=params["rate_shock_bp"],
        deposit_runoff=params["deposit_runoff"],
        credit_loss=params["credit_loss"],
    )
    result = run_stress_scenario(bs, scenario, obs)
    
    st.markdown("### 📊 Sonuçlar")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        render_comparison_card(result.base_lcr, result.stressed_lcr, "LCR")
    with col_r2:
        render_comparison_card(result.base_nsfr, result.stressed_nsfr, "NSFR")
    with col_r3:
        render_comparison_card(result.base_leverage, result.stressed_leverage, "Kaldıraç")
    with col_r4:
        render_comparison_card(result.base_duration_gap, result.stressed_duration_gap, "Duration Gap", suffix=" yıl")
    
    # Trafik ışıkları
    st.markdown("### 🚦 Uyumluluk Kontrolü")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown("**LCR**")
        render_traffic_light(result.stressed_lcr)
    with col_t2:
        st.markdown("**NSFR**")
        render_traffic_light(result.stressed_nsfr)
    with col_t3:
        st.markdown("**Kaldıraç**")
        render_traffic_light(result.stressed_leverage, {"green": 3, "yellow": 2.5})

with tab_custom:
    st.markdown("### 🏛️ Özel Senaryo Oluştur")
    st.caption("Slider'ları kaydırarak kendi kriz senaryonuzu oluşturun ve etkisini görün.")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        fx = st.slider("TL Değer Kaybı (%)", 0, 60, 20, key="custom_fx") / 100
        rate = st.slider("Kâr Payı Artışı (bp)", 0, 1500, 400, step=50, key="custom_rate")
    
    with col_c2:
        deposit = st.slider("Mevduat Kaçışı (%)", 0, 40, 10, key="custom_deposit") / 100
        credit = st.slider("Kredi Değer Kaybı (%)", 0, 20, 5, key="custom_credit") / 100
    
    custom_scenario = StressScenario(
        name="Özel Senaryo",
        fx_shock=fx,
        rate_shock_bp=rate,
        deposit_runoff=deposit,
        credit_loss=credit,
    )
    custom_result = run_stress_scenario(bs, custom_scenario, obs)
    
    st.markdown("### 📊 Özel Senaryo Sonuçları")
    col_cr1, col_cr2, col_cr3, col_cr4 = st.columns(4)
    with col_cr1:
        render_comparison_card(custom_result.base_lcr, custom_result.stressed_lcr, "LCR")
    with col_cr2:
        render_comparison_card(custom_result.base_nsfr, custom_result.stressed_nsfr, "NSFR")
    with col_cr3:
        render_comparison_card(custom_result.base_leverage, custom_result.stressed_leverage, "Kaldıraç")
    with col_cr4:
        render_comparison_card(custom_result.base_duration_gap, custom_result.stressed_duration_gap, "Duration Gap", suffix=" yıl")

with tab_compare:
    st.markdown("### 📊 Tüm Senaryolar Karşılaştırması")
    
    scenarios = load_preset_scenarios()
    all_results = compare_scenarios(bs, obs, scenarios)
    
    # Karşılaştırma grafiği
    fig = create_stress_comparison_chart(all_results)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tablo
    compare_data = {
        "Senaryo": [r.scenario.name for r in all_results],
        "FX Şoku (%)": [r.scenario.fx_shock * 100 for r in all_results],
        "Oran Şoku (bp)": [r.scenario.rate_shock_bp for r in all_results],
        "Stres LCR (%)": [r.stressed_lcr for r in all_results],
        "Stres NSFR (%)": [r.stressed_nsfr for r in all_results],
        "LCR Etki": [r.lcr_impact for r in all_results],
        "LCR Uygun": ["✅" if r.lcr_compliant else "❌" for r in all_results],
        "NSFR Uygun": ["✅" if r.nsfr_compliant else "❌" for r in all_results],
    }
    st.dataframe(compare_data, use_container_width=True, hide_index=True)

# ==============================================================================
# Tornado (Hassasiyet) Analizi
# ==============================================================================
st.markdown("---")
st.markdown("## 🌪️ Hassasiyet (Tornado) Analizi")
st.caption("💡 Her risk faktörünün LCR üzerindeki etkisini ayrı ayrı gösterir. En uzun çubuk, en çok etkileyen faktördür — öncelikli olarak o riske odaklanılmalıdır.")

sensitivities = sensitivity_analysis(bs, obs)
fig = create_tornado_chart(sensitivities)
st.plotly_chart(fig, use_container_width=True)
# Branding
render_footer()
render_developer_watermark()
