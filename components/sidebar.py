# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Sidebar Bileşeni
Veri yükleme, banka bilgileri, tema ve rapor tarihi seçimi.
"""
import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engines.data_generator import (
    generate_balance_sheet, generate_off_balance_sheet,
    generate_profit_pools, generate_yield_curve
)
import config


def render_sidebar():
    """
    Sidebar'ı render eder ve veri kaynağını döndürür.
    
    Returns:
        dict: {
            "balance_sheet": list,
            "off_balance": list,
            "profit_pools": list,
            "yield_curve": dict,
            "bank_name": str,
            "report_date": date,
            "total_assets": float,
        }
    """
    with st.sidebar:
        # Logo ve başlık
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 40px;">{config.APP_ICON}</div>
            <div style="font-size: 22px; font-weight: 700; color: {config.THEME_PRIMARY_COLOR}; margin-top: 6px;">
                {config.APP_TITLE}
            </div>
            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                Basel III Uyumlu Likidite Risk Yönetimi
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Banka Bilgileri
        st.markdown("#### 🏦 Banka Bilgileri")
        bank_name = st.text_input("Banka Adı", value="Örnek Katılım Bankası", key="bank_name")
        report_date = st.date_input("Rapor Tarihi", value=date.today(), key="report_date")
        
        st.divider()
        
        # Veri Kaynağı
        st.markdown("#### 📁 Veri Kaynağı")
        data_source = st.radio(
            "Veri seçin:",
            ["📊 Örnek Veri Kullan", "📤 Excel/CSV Yükle"],
            key="data_source",
            index=0,
        )
        
        if data_source == "📊 Örnek Veri Kullan":
            total_assets = st.slider(
                "Toplam Aktif (Milyar TL)",
                min_value=10, max_value=200, value=50,
                key="total_assets_slider",
            )
            total_assets_tl = total_assets * 1_000_000_000
            
            seed = st.number_input("Veri Seed", value=42, min_value=1, key="seed")
            
            # Veriyi üret
            bs = generate_balance_sheet(seed=seed, total_assets_tl=total_assets_tl)
            obs = generate_off_balance_sheet(seed=seed, total_assets_tl=total_assets_tl)
            pools = generate_profit_pools(bs, seed=seed)
            curve = generate_yield_curve(seed=seed)
            
        else:
            uploaded = st.file_uploader(
                "Excel veya CSV yükleyin",
                type=["xlsx", "csv"],
                key="file_uploader",
            )
            
            total_assets_tl = 50_000_000_000
            
            if uploaded is not None:
                bs, obs = _parse_uploaded_file(uploaded)
                pools = generate_profit_pools(bs)
                curve = generate_yield_curve()
                total_assets_tl = sum(i.amount for i in bs if i.side == "aktif")
            else:
                st.info("📋 Henüz dosya yüklenmedi. Örnek veri kullanılacak.")
                bs = generate_balance_sheet()
                obs = generate_off_balance_sheet()
                pools = generate_profit_pools(bs)
                curve = generate_yield_curve()
        
        st.divider()
        
        # Bilgi
        st.markdown("""
        <div style="font-size: 11px; color: #888; text-align: center; padding: 10px 0;">
            KatılımALM v1.0<br>
            Basel III & BDDK Uyumlu<br>
            IFSB & AAOIFI Standartları
        </div>
        """, unsafe_allow_html=True)
    
    return {
        "balance_sheet": bs,
        "off_balance": obs,
        "profit_pools": pools,
        "yield_curve": curve,
        "bank_name": bank_name,
        "report_date": report_date,
        "total_assets": total_assets_tl,
    }


def _parse_uploaded_file(uploaded):
    """Yüklenen Excel/CSV dosyasını bilanço formatına çevirir."""
    from models import BalanceSheetItem, OffBalanceSheetItem
    
    try:
        if uploaded.name.endswith('.csv'):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded, sheet_name='Bilanço')
        
        items = []
        for _, row in df.iterrows():
            items.append(BalanceSheetItem(
                name=row.get("Kalem Adı", ""),
                amount=float(row.get("Tutar (TL)", 0)),
                currency=row.get("Para Birimi", "TL"),
                side=row.get("Taraf", "aktif"),
                instrument_type=row.get("Enstrüman Tipi", ""),
                islamic_class=row.get("İslami Sınıf", ""),
                maturity_days=int(row.get("Vade (Gün)", 0)),
                repricing_days=int(row.get("Yeniden Fiyatlama (Gün)", 0)),
                profit_rate=float(row.get("Kâr Payı Oranı", 0)),
                is_insured=bool(row.get("Sigortalı", False)),
                counterparty_type=row.get("Karşı Taraf", ""),
                credit_rating=row.get("Kredi Notu", ""),
                hqla_level=row.get("HQLA Seviye", ""),
            ))
        
        # Bilanço dışı
        obs = []
        try:
            if uploaded.name.endswith('.xlsx'):
                uploaded.seek(0)
                df_obs = pd.read_excel(uploaded, sheet_name='Bilanço Dışı')
                for _, row in df_obs.iterrows():
                    obs.append(OffBalanceSheetItem(
                        name=row.get("Kalem Adı", ""),
                        amount=float(row.get("Tutar", 0)),
                        currency=row.get("Para Birimi", "TL"),
                        item_type=row.get("Kalem Tipi", ""),
                        counterparty_type=row.get("Karşı Taraf", ""),
                        maturity_days=int(row.get("Vade (Gün)", 0)),
                        ccf=float(row.get("Kredi Dönüşüm Faktörü", 0.1)),
                    ))
        except Exception:
            obs = generate_off_balance_sheet()
        
        return items, obs
        
    except Exception as e:
        st.error(f"Dosya okuma hatası: {str(e)}")
        bs = generate_balance_sheet()
        obs = generate_off_balance_sheet()
        return bs, obs
