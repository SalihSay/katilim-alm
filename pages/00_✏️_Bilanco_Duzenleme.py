# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Bilanço Düzenleme Sayfası
Aktif ve pasif kalemlerinin tutarlarını interaktif olarak değiştirme imkanı.
Değişiklikler anında LCR/NSFR/Kaldıraç etkisini gösterir.
"""
import streamlit as st
import pandas as pd
import copy
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.branding import render_developer_watermark, render_footer, render_page_copyright

from components.sidebar import render_sidebar
from components.charts import create_gauge_chart, COLORS
from components.metrics import render_kpi_card
from engines.lcr_engine import calculate_lcr
from engines.nsfr_engine import calculate_nsfr
from engines.leverage_ratio import calculate_leverage_ratio
from reports.excel_export import _get_friendly_instrument_name
import config

st.set_page_config(
    page_title=f"{config.APP_TITLE} — Bilanço Düzenleme", 
    page_icon="✏️", layout="wide"
)

data = render_sidebar()
bs = data["balance_sheet"]
obs = data["off_balance"]

st.markdown("# ✏️ Bilanço Düzenleme")
st.markdown("Aktif ve pasif kalemlerinin tutarlarını değiştirin ve *anlık olarak* etkisini görün.")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #EBF5FB 0%, #F8F9FA 100%);
    border-left: 4px solid #3498DB;
    padding: 14px 18px; border-radius: 8px; margin-bottom: 20px;
    font-size: 13px;
">
    💡 <strong>Nasıl kullanılır:</strong> Aşağıdaki tablolarda tutarları değiştirin, 
    ardından <strong>"🔄 Yeniden Hesapla"</strong> butonuna basın. 
    LCR, NSFR ve Kaldıraç oranları anında güncellenecektir.
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# AKTİF TABLOSU (Düzenlenebilir)
# ==============================================================================
st.markdown("---")
st.markdown("## 📗 AKTİF KALEMLERİ (Varlıklar)")

aktif_items = [i for i in bs if i.side == "aktif"]

aktif_table = pd.DataFrame({
    "Kalem Adı": [i.name for i in aktif_items],
    "Açıklama": [_get_friendly_instrument_name(i.instrument_type) for i in aktif_items],
    "Tutar (Milyon TL)": [round(i.amount / 1e6, 1) for i in aktif_items],
    "Para Birimi": [i.currency for i in aktif_items],
    "Kalan Vade (Gün)": [i.maturity_days for i in aktif_items],
    "Yıllık Kâr Payı (%)": [round(i.profit_rate * 100, 2) for i in aktif_items],
})

edited_aktif = st.data_editor(
    aktif_table,
    column_config={
        "Kalem Adı": st.column_config.TextColumn("Kalem Adı", disabled=True, width="medium"),
        "Açıklama": st.column_config.TextColumn("Açıklama", disabled=True, width="large"),
        "Tutar (Milyon TL)": st.column_config.NumberColumn(
            "Tutar (Milyon TL)", min_value=0, format="%.1f", width="small",
            help="Tutarı Milyon TL cinsinden girin"
        ),
        "Para Birimi": st.column_config.SelectboxColumn(
            "Para Birimi", options=["TL", "USD", "EUR", "XAU"], width="small"
        ),
        "Kalan Vade (Gün)": st.column_config.NumberColumn(
            "Kalan Vade", min_value=0, max_value=99999, format="%d", width="small"
        ),
        "Yıllık Kâr Payı (%)": st.column_config.NumberColumn(
            "Kâr Payı (%)", min_value=0, max_value=100, format="%.2f", width="small"
        ),
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="aktif_editor",
)

aktif_toplam = edited_aktif["Tutar (Milyon TL)"].sum()
st.markdown(f"**Aktif Toplamı: {aktif_toplam:,.1f} Milyon TL**")

# ==============================================================================
# PASİF TABLOSU (Düzenlenebilir)
# ==============================================================================
st.markdown("---")
st.markdown("## 📕 PASİF KALEMLERİ (Kaynaklar)")

pasif_items = [i for i in bs if i.side == "pasif"]

pasif_table = pd.DataFrame({
    "Kalem Adı": [i.name for i in pasif_items],
    "Açıklama": [_get_friendly_instrument_name(i.instrument_type) for i in pasif_items],
    "Tutar (Milyon TL)": [round(i.amount / 1e6, 1) for i in pasif_items],
    "Para Birimi": [i.currency for i in pasif_items],
    "Kalan Vade (Gün)": [i.maturity_days if i.maturity_days < 99999 else 0 for i in pasif_items],
    "Yıllık Kâr Payı (%)": [round(i.profit_rate * 100, 2) for i in pasif_items],
})

edited_pasif = st.data_editor(
    pasif_table,
    column_config={
        "Kalem Adı": st.column_config.TextColumn("Kalem Adı", disabled=True, width="medium"),
        "Açıklama": st.column_config.TextColumn("Açıklama", disabled=True, width="large"),
        "Tutar (Milyon TL)": st.column_config.NumberColumn(
            "Tutar (Milyon TL)", min_value=0, format="%.1f", width="small",
            help="Tutarı Milyon TL cinsinden girin"
        ),
        "Para Birimi": st.column_config.SelectboxColumn(
            "Para Birimi", options=["TL", "USD", "EUR", "XAU"], width="small"
        ),
        "Kalan Vade (Gün)": st.column_config.NumberColumn(
            "Kalan Vade", min_value=0, max_value=99999, format="%d", width="small"
        ),
        "Yıllık Kâr Payı (%)": st.column_config.NumberColumn(
            "Kâr Payı (%)", min_value=0, max_value=100, format="%.2f", width="small"
        ),
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="pasif_editor",
)

pasif_toplam = edited_pasif["Tutar (Milyon TL)"].sum()
st.markdown(f"**Pasif Toplamı: {pasif_toplam:,.1f} Milyon TL**")

# Bilanço dengesi kontrolü
fark = aktif_toplam - pasif_toplam
if abs(fark) < 0.5:
    st.success("✅ **Bilanço dengede.** Aktif = Pasif")
else:
    st.warning(f"⚠️ **Bilanço dengesiz!** Fark: {fark:,.1f} Milyon TL — Aktiflerin ve pasiflerin eşit olması gerekir.")

# ==============================================================================
# YENİDEN HESAPLA BUTONU
# ==============================================================================
st.markdown("---")

if st.button("🔄 Değişiklikleri Uygula ve Yeniden Hesapla", type="primary", use_container_width=True):
    
    # Düzenlenmiş verileri balance sheet'e geri yaz
    modified_bs = []
    
    for idx, item in enumerate(aktif_items):
        new_item = copy.deepcopy(item)
        new_item.amount = edited_aktif.iloc[idx]["Tutar (Milyon TL)"] * 1e6
        new_item.currency = edited_aktif.iloc[idx]["Para Birimi"]
        new_item.maturity_days = int(edited_aktif.iloc[idx]["Kalan Vade (Gün)"])
        new_item.profit_rate = edited_aktif.iloc[idx]["Yıllık Kâr Payı (%)"] / 100
        modified_bs.append(new_item)
    
    for idx, item in enumerate(pasif_items):
        new_item = copy.deepcopy(item)
        new_item.amount = edited_pasif.iloc[idx]["Tutar (Milyon TL)"] * 1e6
        new_item.currency = edited_pasif.iloc[idx]["Para Birimi"]
        vade = int(edited_pasif.iloc[idx]["Kalan Vade (Gün)"])
        new_item.maturity_days = vade if vade > 0 else item.maturity_days
        new_item.profit_rate = edited_pasif.iloc[idx]["Yıllık Kâr Payı (%)"] / 100
        modified_bs.append(new_item)
    
    # Yeniden hesapla
    new_lcr = calculate_lcr(modified_bs, obs)
    new_nsfr = calculate_nsfr(modified_bs, obs)
    new_lev = calculate_leverage_ratio(modified_bs, obs)
    
    # Orijinal değerler
    orig_lcr = calculate_lcr(bs, obs)
    orig_nsfr = calculate_nsfr(bs, obs)
    orig_lev = calculate_leverage_ratio(bs, obs)
    
    st.markdown("### 📊 Güncellenmiş Sonuçlar")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_lcr = new_lcr.lcr_ratio - orig_lcr.lcr_ratio
        status = "success" if new_lcr.lcr_ratio >= 100 else "danger"
        render_kpi_card(
            "Likidite Karşılama (LCR)", 
            f"%{new_lcr.lcr_ratio:.1f}",
            target="Min: %100", 
            status=status,
            delta=f"{delta_lcr:+.1f}%",
            icon="💧"
        )
        fig = create_gauge_chart(new_lcr.lcr_ratio, "Yeni LCR", 0, 250, 100)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        delta_nsfr = new_nsfr.nsfr_ratio - orig_nsfr.nsfr_ratio
        status = "success" if new_nsfr.nsfr_ratio >= 100 else "danger"
        render_kpi_card(
            "Kararlı Fonlama (NSFR)", 
            f"%{new_nsfr.nsfr_ratio:.1f}",
            target="Min: %100", 
            status=status,
            delta=f"{delta_nsfr:+.1f}%",
            icon="🏗️"
        )
        fig = create_gauge_chart(new_nsfr.nsfr_ratio, "Yeni NSFR", 0, 250, 100)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        delta_lev = new_lev.leverage_ratio - orig_lev.leverage_ratio
        status = "success" if new_lev.leverage_ratio >= 3 else "danger"
        render_kpi_card(
            "Kaldıraç Oranı", 
            f"%{new_lev.leverage_ratio:.1f}",
            target="Min: %3",
            status=status,
            delta=f"{delta_lev:+.1f}%",
            icon="⚖️"
        )
        fig = create_gauge_chart(new_lev.leverage_ratio, "Yeni Kaldıraç", 0, 15, 3)
        st.plotly_chart(fig, use_container_width=True)
    
    # Karşılaştırma tablosu
    st.markdown("### 📋 Önceki vs. Yeni Karşılaştırma")
    compare_df = pd.DataFrame({
        "Gösterge": ["Likidite Karşılama (LCR)", "Kararlı Fonlama (NSFR)", "Kaldıraç Oranı"],
        "Önceki Değer": [
            f"%{orig_lcr.lcr_ratio:.1f}", 
            f"%{orig_nsfr.nsfr_ratio:.1f}",
            f"%{orig_lev.leverage_ratio:.1f}"
        ],
        "Yeni Değer": [
            f"%{new_lcr.lcr_ratio:.1f}", 
            f"%{new_nsfr.nsfr_ratio:.1f}",
            f"%{new_lev.leverage_ratio:.1f}"
        ],
        "Değişim": [
            f"{delta_lcr:+.1f}%", 
            f"{delta_nsfr:+.1f}%",
            f"{delta_lev:+.1f}%"
        ],
        "BDDK Limiti": ["Min %100", "Min %100", "Min %3"],
        "Durum": [
            "✅ Uygun" if new_lcr.is_compliant else "❌ Yetersiz",
            "✅ Uygun" if new_nsfr.is_compliant else "❌ Yetersiz",
            "✅ Uygun" if new_lev.is_compliant else "❌ Yetersiz",
        ],
    })
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

# Branding & Telif
render_footer()
render_developer_watermark()
