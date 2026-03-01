# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Raporlar Sayfası
Formatlı Excel export, rapor önizleme.
"""
import streamlit as st
import pandas as pd
from io import BytesIO
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer

from components.sidebar import render_sidebar
from components.metrics import render_kpi_card
from engines.lcr_engine import calculate_lcr, calculate_lcr_by_currency
from engines.nsfr_engine import calculate_nsfr
from engines.leverage_ratio import calculate_leverage_ratio
from engines.duration_calc import portfolio_duration, duration_gap
from engines.gap_analysis import build_gap_table
from engines.stress_test import compare_scenarios
from engines.profit_pool import calculate_all_pools
from reports.excel_export import create_formatted_excel
import config

st.set_page_config(page_title=f"{config.APP_TITLE} — Raporlar", page_icon="📄", layout="wide")

data = render_sidebar()
bs = data["balance_sheet"]
obs = data["off_balance"]
bank_name = data["bank_name"]
report_date = data["report_date"]

st.markdown("# 📄 BDDK Rapor Çıktısı")
st.markdown("Tüm sonuçları **formatlı Excel** olarak indirin. Başlıklar renkli, sütunlar otomatik genişletilmiş, tutarlar para birimi ile gösterilmiştir.")

# ==============================================================================
# Rapor Tipi Seçimi
# ==============================================================================
report_type = st.selectbox(
    "Rapor Tipi Seçin",
    ["📊 Likidite Oranları Raporu", "🏗️ Fonlama Yapısı Raporu", "📐 Faiz Riski Raporu", "📑 Tam Kapsamlı Rapor"],
    key="report_type",
)

# ==============================================================================
# Hesaplamalar
# ==============================================================================

@st.cache_data
def compute_all_metrics(_bs, _obs):
    lcr = calculate_lcr(_bs, _obs)
    lcr_by_cur = calculate_lcr_by_currency(_bs, _obs)
    nsfr = calculate_nsfr(_bs, _obs)
    leverage = calculate_leverage_ratio(_bs, _obs)
    
    total_aktif = sum(i.amount for i in _bs if i.side == "aktif")
    total_pasif = sum(i.amount for i in _bs if i.side == "pasif")
    a_dur = portfolio_duration(_bs, "aktif")
    p_dur = portfolio_duration(_bs, "pasif")
    dur_gap_val = duration_gap(a_dur, p_dur, total_aktif, total_pasif)
    
    gap_table = build_gap_table(_bs)
    stress_results = compare_scenarios(_bs, _obs)
    pool_result = calculate_all_pools(_bs)
    
    return {
        "lcr": lcr, "lcr_by_cur": lcr_by_cur, "nsfr": nsfr,
        "leverage": leverage, "dur_gap": dur_gap_val,
        "a_dur": a_dur, "p_dur": p_dur,
        "gap_table": gap_table, "stress": stress_results,
        "pools": pool_result,
    }

metrics = compute_all_metrics(bs, obs)

# ==============================================================================
# Rapor Önizleme
# ==============================================================================
st.markdown("### 📋 Rapor Önizleme")

col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    render_kpi_card("Likidite Karşılama (LCR)", f"%{metrics['lcr'].lcr_ratio:.1f}", 
                    status="success" if metrics['lcr'].is_compliant else "danger", icon="💧")
with col_p2:
    render_kpi_card("Kararlı Fonlama (NSFR)", f"%{metrics['nsfr'].nsfr_ratio:.1f}",
                    status="success" if metrics['nsfr'].is_compliant else "danger", icon="🏗️")
with col_p3:
    dur_s = "success" if abs(metrics['dur_gap']) < 2 else "warning"
    render_kpi_card("Vade Uyumsuzluğu", f"{metrics['dur_gap']:.2f} yıl", status=dur_s, icon="📐")
with col_p4:
    render_kpi_card("Kaldıraç Oranı", f"%{metrics['leverage'].leverage_ratio:.1f}",
                    status="success" if metrics['leverage'].is_compliant else "danger", icon="⚖️")

# ==============================================================================
# Excel Export
# ==============================================================================
st.markdown("---")
st.markdown("### 📥 Excel Rapor İndir")

excel_data = create_formatted_excel(bs, obs, metrics, bank_name, report_date, report_type)

st.download_button(
    label="📥 Formatlı Excel Rapor İndir",
    data=excel_data,
    file_name=f"KatilimALM_Rapor_{report_date.strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
)

st.markdown("""
<div style="
    background: linear-gradient(135deg, #EBF5FB 0%, #FFFFFF 100%);
    border-left: 4px solid #2980B9;
    padding: 20px; border-radius: 8px; margin-top: 20px;
">
    <strong>📋 Rapor İçeriği (10 Sayfa):</strong><br><br>
    <table style="width: 100%; font-size: 13px;">
        <tr><td>📌 <b>Kapak</b></td><td>Banka bilgileri, rapor tarihi, toplam aktif/pasif</td></tr>
        <tr><td>📊 <b>Yönetici Özeti</b></td><td>LCR, NSFR, Kaldıraç, Vade Uyumsuzluğu — uygun/aşım</td></tr>
        <tr><td>📋 <b>Bilanço</b></td><td>Tüm kalemler, TL karşılığı, para birimi, kâr payı oranı</td></tr>
        <tr><td>🔴 <b>LCR Nakit Çıkışları</b></td><td>30 günlük çıkışlar, kaçış oranı, kaynak</td></tr>
        <tr><td>🟢 <b>LCR Nakit Girişleri</b></td><td>30 günlük girişler, giriş oranı</td></tr>
        <tr><td>📈 <b>NSFR Kararlı Fonlama</b></td><td>Fonlama kaynakları, ağırlıklar, ASF katkısı</td></tr>
        <tr><td>📉 <b>NSFR Gerekli Fonlama</b></td><td>Varlık gereksinimleri, ağırlıklar, RSF gereksinimi</td></tr>
        <tr><td>📊 <b>Vade Uyumsuzluğu</b></td><td>7 vade aralığı, açık/fazla, birikimli gap</td></tr>
        <tr><td>⚡ <b>Stres Testi</b></td><td>5 kriz senaryosu, sonuçlar, uygunluk durumu</td></tr>
        <tr><td>💰 <b>Kâr Payı Havuzları</b></td><td>Havuz performansı, fon kullanımı, dağıtılan kâr payı</td></tr>
    </table>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    background: #FEF9E7; border-left: 4px solid #F39C12;
    padding: 14px; border-radius: 8px; margin-top: 12px; font-size: 12px;
">
    ✨ <strong>Excel Formatlama:</strong> Başlıklar lacivert arka plan, 
    otomatik sütun genişliği, sayısal değerler binlik ayırıcı ile (1.234.567 TL), 
    uygun/aşım durumları renkli, alternatif satır renklendirmesi.
</div>
""", unsafe_allow_html=True)
# Branding
render_footer()
render_developer_watermark()
